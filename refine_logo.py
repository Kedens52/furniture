from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
from collections import defaultdict

BASE=Path(__file__).parent
SOURCES=[Path('C:/Users/8523~1/AppData/Local/Temp/codex-clipboard-c94682d2-9788-4107-9c55-55bfa2b93bd1.png'),Path('C:/Users/8523~1/AppData/Local/Temp/codex-clipboard-3d4a612d-04b1-4a4c-8bd5-aec302eceefd.png')]

def contours(mask):
    p=np.pad(mask,1); edges=defaultdict(list)
    for typ,side in enumerate([~p[:-2,1:-1],~p[1:-1,2:],~p[2:,1:-1],~p[1:-1,:-2]]):
        ys,xs=np.where(mask & side)
        for x,y in zip(xs.tolist(),ys.tolist()):
            if typ==0: a,b=(x,y),(x+1,y)
            elif typ==1: a,b=(x+1,y),(x+1,y+1)
            elif typ==2: a,b=(x+1,y+1),(x,y+1)
            else: a,b=(x,y+1),(x,y)
            edges[a].append(b)
    loops=[]
    while edges:
        start=next(iter(edges)); pt=start; poly=[]
        for _ in range(100000):
            poly.append(pt); opts=edges[pt]; nxt=opts.pop()
            if not opts: del edges[pt]
            pt=nxt
            if pt==start: break
        if len(poly)>7:
            arr=np.array(poly,dtype=float)
            area=np.sum(arr[:,0]*np.roll(arr[:,1],-1)-arr[:,1]*np.roll(arr[:,0],-1))/2
            if abs(area)>3: loops.append((arr,area))
    return sorted(loops,key=lambda z:-abs(z[1]))

def rdp(p,eps):
    if len(p)<3:return p
    v=p[-1]-p[0]; den=np.linalg.norm(v)
    if den<1e-9: d=np.linalg.norm(p-p[0],axis=1)
    else: d=np.abs(v[0]*(p[:,1]-p[0,1])-v[1]*(p[:,0]-p[0,0]))/den
    i=np.argmax(d)
    if d[i]<=eps:return p[[0,-1]]
    return np.concatenate([rdp(p[:i+1],eps)[:-1],rdp(p[i:],eps)])

def norm(v):
    n=np.linalg.norm(v); return v/n if n>1e-10 else np.array([1.,0.])

def fit(p,t1,t2,error,depth=0):
    if len(p)==2:
        d=np.linalg.norm(p[1]-p[0])/3
        return [(p[0],p[0]+t1*d,p[-1]+t2*d,p[-1])]
    ds=np.linalg.norm(np.diff(p,axis=0),axis=1); u=np.concatenate([[0],np.cumsum(ds)]);u/=u[-1]
    b0=(1-u)**3;b1=3*u*(1-u)**2;b2=3*u*u*(1-u);b3=u**3
    a1=b1[:,None]*t1; a2=b2[:,None]*t2
    rhs=p-(b0+b1)[:,None]*p[0]-(b2+b3)[:,None]*p[-1]
    C=np.array([[np.sum(a1*a1),np.sum(a1*a2)],[np.sum(a1*a2),np.sum(a2*a2)]])
    X=np.array([np.sum(a1*rhs),np.sum(a2*rhs)])
    try: alpha=np.linalg.solve(C,X)
    except np.linalg.LinAlgError: alpha=np.array([-1,-1])
    dist=np.linalg.norm(p[-1]-p[0]); default=dist/3
    if min(alpha)<dist*1e-6 or max(alpha)>max(u[-1],dist)*3:alpha=np.array([default,default])
    q=(p[0],p[0]+alpha[0]*t1,p[-1]+alpha[1]*t2,p[-1])
    calc=b0[:,None]*q[0]+b1[:,None]*q[1]+b2[:,None]*q[2]+b3[:,None]*q[3]
    err=np.linalg.norm(calc-p,axis=1);idx=int(np.argmax(err))
    if err[idx]<error or depth>18:return [q]
    idx=max(1,min(len(p)-2,idx));tc=norm(p[idx-1]-p[idx+1])
    return fit(p[:idx+1],t1,tc,error,depth+1)+fit(p[idx:],-tc,t2,error,depth+1)

def curve_path(poly,error=.72):
    # Smooth only the pixel staircase, keeping real corners as fixed anchors.
    n=len(poly); smooth=(np.roll(poly,2,0)+2*np.roll(poly,1,0)+4*poly+2*np.roll(poly,-1,0)+np.roll(poly,-2,0))/10
    split=n//2
    reduced=np.concatenate([rdp(smooth[:split+1],1.2)[:-1],rdp(np.concatenate([smooth[split:],smooth[:1]]),1.2)[:-1]])
    corners=[]
    for i,p in enumerate(reduced):
        a=norm(p-reduced[i-1]);b=norm(reduced[(i+1)%len(reduced)]-p)
        if np.dot(a,b)<.60:
            corners.append(int(np.argmin(np.linalg.norm(smooth-p,axis=1))))
    if len(corners)<2:corners=[0,split]
    corners=sorted(set(corners)); segs=[]
    for j,k in enumerate(corners):
        end=corners[(j+1)%len(corners)]
        pp=smooth[k:end+1] if end>k else np.concatenate([smooth[k:],smooth[:end+1]])
        if len(pp)>1:segs.extend(fit(pp,norm(pp[min(3,len(pp)-1)]-pp[0]),norm(pp[max(0,len(pp)-4)]-pp[-1]),error))
    f=lambda p:f'{p[0]:.2f},{p[1]:.2f}'
    return 'M'+f(segs[0][0])+''.join(' C'+f(q[1])+' '+f(q[2])+' '+f(q[3]) for q in segs)+' Z'

def maskpath(mask,color,minarea=4,error=.72):
    loops=contours(mask)
    ds=[curve_path(p,error) for p,a in loops if abs(a)>=minarea]
    return f'<path fill="{color}" fill-rule="evenodd" d="'+ ' '.join(ds)+'"/>' if ds else ''

def nearest(a,palette):
    return np.argmin(np.sum((a[:,:,None,:].astype(float)-np.array(palette)[None,None,:,:])**2,axis=-1),axis=-1)

def make_main():
    img=Image.open(SOURCES[0]).convert('RGB').crop((195,170,1035,565))
    a=np.array(img.filter(ImageFilter.MedianFilter(3)))
    # Source palette retained; discard only scan noise and compression shades.
    pal=[(255,255,255),(83,4,27),(173,0,42),(213,0,49),(241,0,55),(255,45,96),(255,128,0),(255,180,16),(255,224,79)]
    labels=nearest(a,pal)
    colored=labels!=0
    valid=np.zeros(colored.shape,dtype=bool)
    # Outer white keyline follows the actual colored silhouette.
    expanded=np.array(Image.fromarray((colored*255).astype('uint8')).filter(ImageFilter.MaxFilter(17)))>0
    body=[]
    outer=[(p,ar) for p,ar in contours(expanded) if ar>150]
    body.append('<g id="White-keyline">'+''.join('<path fill="#ffffff" d="'+curve_path(p,1.0)+'"/>' for p,ar in outer)+'</g>')
    # Exact-size substrate prevents hairline gaps between adjacent color shapes.
    body.append('<g id="Original-color-shapes">')
    for idx in [4,3,2,1,6,7,8,5]:
        color='#%02x%02x%02x'%pal[idx]
        m=labels==idx
        body.append(maskpath(m,color,7,.78))
    body.append('</g>')
    # White lettering is isolated from the surrounding background, with all counters retained.
    whites=contours(labels==0)
    letterpaths=[]
    for p,ar in whites:
        if ar>75 and ar<18000:
            letterpaths.append('<path fill="#ffffff" d="'+curve_path(p,.58)+'"/>')
    # Their counters use source colors already visible beneath evenodd compound shapes.
    # Use each bounded white component together with contained negative loops.
    body=body[:-0] if False else body
    body.append('<g id="Original-letter-outlines">')
    for p,ar in whites:
        if not (75<ar<18000):continue
        xmin,ymin=p.min(0);xmax,ymax=p.max(0)
        holes=[]
        for hp,ha in whites:
            if ha<0 and abs(ha)>7 and np.all(hp.min(0)>=[xmin,ymin]) and np.all(hp.max(0)<=[xmax,ymax]):holes.append(hp)
        d=curve_path(p,.58)+' '.join(curve_path(hp,.58) for hp in holes)
        body.append('<path fill="#ffffff" fill-rule="evenodd" d="'+d+'"/>')
    body.append('</g>')
    return ''.join(body),840,395

def make_horizontal():
    a=np.array(Image.open(SOURCES[1]).convert('RGB'))
    pal=[(255,255,255),(251,246,246),(222,9,85),(82,5,32),(247,149,30),(165,3,58)]
    labels=nearest(a,pal)
    body=['<g id="Horizontal-original-proportions">']
    for idx in [1,2,4,5,3]:
        m=labels==idx
        body.append(maskpath(m,'#%02x%02x%02x'%pal[idx],3,.7))
    body.append('</g>')
    return ''.join(body),654,135

def svg(body,w,h):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*2}" height="{h*2}" viewBox="0 0 {w} {h}"><g>{body}</g></svg>'

main,w,h=make_main(); horizontal,hw,hh=make_horizontal()
(BASE/'Race-Burger_Refined_Main.svg').write_text(svg(main,w,h),encoding='utf-8')
(BASE/'Race-Burger_Refined_Horizontal.svg').write_text(svg(horizontal,hw,hh),encoding='utf-8')
preview='<rect width="1400" height="940" fill="#f5f3f0"/><g transform="translate(40 40) scale(1.57)">'+main+'</g><g transform="translate(46 710) scale(2)">'+horizontal+'</g>'
(BASE/'Race-Burger_Refined_Preview.svg').write_text(svg(preview,1400,1040),encoding='utf-8')
print('Faithful source geometry reconstructed as cubic Bezier paths.')
