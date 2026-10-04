#target illustrator
(function(){
 var base=File($.fileName).parent;
 var doc=app.activeDocument;
 var old=doc.layers.getByName('02 - HORIZONTAL / Editable vector artwork');
 var hdoc=app.open(File(base.fsName+'/Race-Burger_Horizontal.svg'));
 var root=hdoc.layers[0].groupItems[0];
 var layer=doc.layers.add(); layer.name='Horizontal rebuilt';
 var copy=root.duplicate(layer,ElementPlacement.PLACEATBEGINNING);
 hdoc.close(SaveOptions.DONOTSAVECHANGES); app.activeDocument=doc;
 old.remove(); layer.name='02 - HORIZONTAL / Editable vector artwork';
 var scale=1600/copy.width*100; copy.resize(scale,scale,true,true,true,true,scale); copy.position=[60,-140];
 doc.artboards.setActiveArtboardIndex(1);
 var png=new ExportOptionsPNG24(); png.transparency=true; png.antiAliasing=true; png.artBoardClipping=true; png.horizontalScale=200; png.verticalScale=200;
 doc.exportFile(File(base.fsName+'/Race-Burger_Horizontal.png'),ExportType.PNG24,png);
 doc.artboards.setActiveArtboardIndex(0);
 app.executeMenuCommand('fitall'); doc.save();
})();
