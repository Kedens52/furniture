#target illustrator
(function () {
    var base = File($.fileName).parent;
    var report = File(base.fsName + '/Illustrator-verification.txt');
    try {
        var doc = app.open(File(base.fsName + '/Race-Burger_Main.svg'));
        doc.layers[0].name = '01 - MAIN / Editable vector artwork';
        doc.artboards[0].name = '01 - Main logo';
        var hdoc = app.open(File(base.fsName + '/Race-Burger_Horizontal.svg'));
        var root = hdoc.groupItems.add(); root.name = 'Horizontal logo';
        for (var i = hdoc.pageItems.length - 1; i >= 0; i--) {
            var item = hdoc.pageItems[i];
            if (item !== root && item.parent.typename === 'Layer') item.move(root, ElementPlacement.PLACEATBEGINNING);
        }
        var layer = doc.layers.add(); layer.name = '02 - HORIZONTAL / Editable vector artwork';
        var copied = root.duplicate(layer, ElementPlacement.PLACEATBEGINNING);
        hdoc.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;
        var scale = 1600 / copied.width * 100;
        copied.resize(scale, scale, true, true, true, true, scale);
        copied.position = [60, -140];
        var bottom = -140 - copied.height - 60;
        doc.artboards.add([0, -80, 1720, bottom]);
        doc.artboards[1].name = '02 - Horizontal logo';
        var palette = [['Race Red',235,0,62],['Deep Red',185,0,50],['Burgundy',87,5,31],['Orange',255,130,0],['Yellow',255,189,34],['White',255,255,255]];
        for (var c = 0; c < palette.length; c++) { var sw = doc.swatches.add(); sw.name = palette[c][0]; var color = new RGBColor(); color.red = palette[c][1]; color.green = palette[c][2]; color.blue = palette[c][3]; sw.color = color; }
        doc.artboards.setActiveArtboardIndex(0);
        doc.selection = null;
        var opts = new IllustratorSaveOptions(); opts.pdfCompatible = true; opts.compressed = true; opts.embedICCProfile = true;
        doc.saveAs(File(base.fsName + '/Race-Burger_Master.ai'), opts);
        for (var a = 0; a < 2; a++) {
            doc.artboards.setActiveArtboardIndex(a);
            var png = new ExportOptionsPNG24(); png.transparency = true; png.antiAliasing = true; png.artBoardClipping = true; png.horizontalScale = 200; png.verticalScale = 200;
            doc.exportFile(File(base.fsName + (a === 0 ? '/Race-Burger_Main.png' : '/Race-Burger_Horizontal.png')), ExportType.PNG24, png);
        }
        doc.artboards.setActiveArtboardIndex(0);
        app.executeMenuCommand('fitall');
        doc.save();
        report.open('w'); report.write('Native Adobe Illustrator document saved.\nArtboards: ' + doc.artboards.length + '\nVector paths: ' + doc.pathItems.length + '\nRaster items: ' + doc.rasterItems.length + '\nPlaced items: ' + doc.placedItems.length + '\nText objects: ' + doc.textFrames.length + '\n'); report.close();
    } catch (e) { report.open('w'); report.write('ERROR: ' + e + '\nLine: ' + e.line); report.close(); }
})();
