
const plotter = (function() {
    return {
        plotBandColor: 'rgba(79, 190, 255, 0.1)',

        draw: async function(plotData, renderTo) 
        {
            // We will present only runs that are present in all series
            if(plotData.series.length > 1) {
                // Find a common subset of runs
                const allRuns = {}
                plotData.series.forEach(series => {
                    series.trends.forEach(trend => {
                        allRuns[trend.run] = (allRuns[trend.run] ? allRuns[trend.run] : 0) + 1
                    })
                })

                const runsToRemove = []
                for(let key in allRuns) {
                    if(allRuns[key] < plotData.series.length) {
                        runsToRemove.push(parseInt(key))
                    }
                }
                
                // Remove runs that are not present in every series
                plotData.series.forEach(series => {
                    series.trends = series.trends.filter(trend => !runsToRemove.includes(trend.run))
                })
            }

            if(plotData.correlation) 
            {
                if(plotData.series.length === 2 || plotData.series.length === 3)
                    return this.drawCorrelationPlot(plotData, renderTo)
                else
                    return null
            }

            if(optionsController.options.showXRange || optionsController.options.showDeliveredLumi)
                return this.drawXRangePlot(plotData, renderTo)
            else if(optionsController.options.showDatetime)
                return this.drawXRangeDatetimePlot(plotData, renderTo)
            else
                return this.drawScatterPlot(plotData, renderTo)
        },

        drawCorrelationPlot: function(plotData, renderTo)
        {
            const is3d = plotData.series.length === 3
            const plotName = plotData.plot_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const seriesTitles = plotData.series.map(x => x.metadata.plot_title)

            // First array contains x values and second array contains y values
            const values = yValues[0].map((v, i) => {
                const obj = {
                    x: v,
                    y: yValues[1][i],
                    run: xValues[i],
                    marker: {
                        fillColor: helpers.colorScale((xValues[i] - xValues[0]) / (xValues[xValues.length - 1] - xValues[0])),
                        radius: 4,
                    }
                }

                if (is3d)
                    obj.z = yValues[2][i]

                return obj
            })

            const options = {
                credits: {
                    enabled: false
                },
                chart: {
                    type: is3d ? "scatter3d" : "scatter",
                    renderTo: renderTo,
                    zoomType: is3d ? "none" : "xy",
                    animation: false,

                    options3d: {
                        enabled: is3d,
                        alpha: 30,
                        beta: 30,
                        depth: 400,
                        viewDistance: 20,
                    }
                },
                lang: {
                    noData: "No data found"
                },
                title: {
                    text: plotName,
                    useHTML: true
                },
                subtitle: {
                    text: `<i>${plotData.name}</i>`
                },
                xAxis: {
                    title: {
                        text: seriesTitles[0],
                    },
                    max: Math.max(...values.map(i => i.x)),
                    min: Math.min(...values.map(i => i.x))
                },
                yAxis: {
                    title: {
                        text: seriesTitles[1],
                    },
                },
                zAxis: is3d ? {
                    title: {
                        text: seriesTitles[2],
                    },
                } : undefined,
                legend: {
                    useHTML: true 
                },
                tooltip: {
                    headerFormat: "",
                    pointFormat: 
                        is3d ? 
                        `<b>Run No:</b> {point.run}<br><b>${seriesTitles[0]}</b>: {point.x}<br><b>${seriesTitles[1]}</b>: {point.y}<br><b>${seriesTitles[2]}</b>: {point.z}` :
                        `<b>Run No:</b> {point.run}<br><b>${seriesTitles[0]}</b>: {point.x}<br><b>${seriesTitles[1]}</b>: {point.y}`,
                    style : { opacity: 0.9 },
                },
                series: [{
                        type: is3d ? "scatter3d" : "scatter",
                        name: "Correlation",
                        data: values,
                        animation: false,
                        marker: {
                            symbol: "circle",
                        },
                        color: "#000000",
                        turboThreshold: 2000
                    }
                ],
                colorAxis: {
                    min: xValues[0],
                    max: xValues[xValues.length - 1],
                    minColor: "#00FF00",
                    maxColor: "#FF0000",
                    stops: [
                        [0, "#00FF00"],
                        [0.5, "#FFFF00"],
                        [1, "#FF0000"]
                    ]
                },
            }

            if(optionsController.options.showRegression)
            {
                if(!is3d)
                {
                    const regression = helpers.linearRegression(values)
                    const regressionData = regression[0]
                    const regressionEquation = regression[1]

                    options.series.push({
                        type: "line",
                        name: regressionEquation,
                        data: regressionData,
                        marker: {
                            enabled: false
                        },
                        enableMouseTracking: false,
                        animation: false,
                    })
                }
                else
                {
                    // Polygon in 3D is not currently supported in Highcharts
                }   
            }

            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            if(is3d) 
            {
                // 3D panning and rotating functionality
                function dragStart(eStart) {
                    eStart = chartObj.pointer.normalize(eStart)
            
                    const posX = eStart.chartX
                    const posY = eStart.chartY
                    const alpha = chartObj.options.chart.options3d.alpha
                    const beta = chartObj.options.chart.options3d.beta
                    const sensitivity = 3  // lower is more sensitive
                    const handlers = []

                    function drag(e) {
                        // Get e.chartX and e.chartY
                        e = chartObj.pointer.normalize(e)
            
                        chartObj.update({
                            chart: {
                                options3d: {
                                    alpha: alpha + (e.chartY - posY) / sensitivity,
                                    beta: beta + (posX - e.chartX) / sensitivity
                                }
                            }
                        }, undefined, undefined, false)
                    }

                    function unbindAll() {
                        handlers.forEach(function (unbind) {
                            if (unbind) {
                                unbind()
                            }
                        })
                        handlers.length = 0
                    }

                    handlers.push(Highcharts.addEvent(document, 'mousemove', drag))
                    handlers.push(Highcharts.addEvent(document, 'touchmove', drag))
                    
                    handlers.push(Highcharts.addEvent(document, 'mouseup', unbindAll))
                    handlers.push(Highcharts.addEvent(document, 'touchend', unbindAll))
                }
                Highcharts.addEvent(chartObj.container, 'mousedown', dragStart)
                Highcharts.addEvent(chartObj.container, 'touchstart', dragStart)
            }

            return chartObj
        },

        drawScatterPlot: function(plotData, renderTo) 
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const durations = plotData.series[0].trends.map(x => x.oms_info.duration)
            const seriesTitles = plotData.series.map(x => x.metadata.plot_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]

            const bands = this.getScatterFillBands(xValues, fills)

            const options = {
                credits: {
                    enabled: false
                },
                chart: {
                    renderTo: renderTo,
                    zoomType: "xy",
                    animation: false,
                },
                lang: {
                    noData: "No data found"
                },
                title: {
                    text: plotName,
                    useHTML: true
                },
                subtitle: {
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
                    useHTML: true
                },
                xAxis: {
                    title: {
                        text: "Run No.",
                    },
                    categories: [...new Set([].concat(...xValues))], 
                    plotBands: optionsController.options.showFills ? bands : []
                },
                yAxis: [
                    {
                        title: {
                            text: yTitle,
                            useHTML: true
                        },
                        min: min_y,
                        max: max_y,
                        tickPixelInterval: 60,
                    },
                    {
                        zoomEnabled: false,
                        title: {
                            text: "Run Duration (sec)",
                        },
                        opposite: true,
                        visible: optionsController.options.showDurations && durations !== undefined,
                        tickPixelInterval: 60
                    }
                ],
                legend: {
                    useHTML: true 
                },
                plotOptions: {
                    series: {
                        // Make sure legend click toggles the visibility of fill lines
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
                                    const plotBands = this.chart.xAxis[0].plotLinesAndBands;
                                    if (!this.visible) {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                        }
                                    }
                                    else {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                        }
                                    }
                                }
                            }
                        } : {},
                        allowPointSelect: true,
                        turboThreshold: 2000,
                        point: {
                            events: {
                                click: function () {
                                    const parent = $(this.series.chart.container).parent().parent()

                                    if(fullScreenController.isFullScreen) {
                                        fullScreenController.selectDataPoint(this.series_index, this.index)
                                    }
                                    else {
                                        main.updateLinks(parent, plotData, this.category, this.series_index)
                                    }
                                },
                                unselect: function () {
                                    // Disable deselection
                                    return false
                                }
                            }
                        },
                        marker: {
                            symbol: "circle"
                        }
                    },
                },
                series: optionsController.options.showFills ?
                    [{ // "Fills" legend item
                        name: "Fills",
                        color: this.plotBandColor,
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            for(let i = 0; i < plotData.series.length; i++)
            {
                const tooltip = `
                    <b>Value:</b> {point.y_readable}<br>
                    <b>Error:</b> {point.error_readable}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Duration:</b> {point.duration_readable}<br/>
                    <b>Delivered luminosity:</b> {point.del_lumi} <i>pb<sup>-1</sup></i><br/>
                    <b>Start time:</b> {point.start_time}<br/>
                    <b>End time:</b> {point.end_time}<br/>
                    Click on the data point to reveal more info.`

                const data = plotData.series[i].trends.map(trend => ({
                    y:                  trend.value,
                    error:              trend.error,
                    y_readable:         helpers.toExponential(trend.value, 2),
                    error_readable:     helpers.toExponential(trend.error, 2),
                    run:                trend.run,
                    series_index:       i,
                    duration_readable:  helpers.secondsToHHMMSS(trend.oms_info.duration),
                    del_lumi:           parce_lumi(trend.oms_info.delivered_lumi),
                    start_time:         trend.oms_info.start_time,
                    end_time:           trend.oms_info.end_time
                }))

                const pointRadius = data.length > 80 ? 3 : 3.5

                options.series.push({
                    name: seriesTitles[i],
                    type: "scatter",
                    data: data,
                    color: helpers.seriesColors[i],
                    borderWidth: 20,
                    marker: {
                        radius: pointRadius,
                        lineWidth: 1,
                        lineColor: helpers.seriesColors[i],
                    },
                    tooltip: {
                        pointFormat: tooltip,
                    },
                    showInLegend: true,
                    animation: false,
                    states: {
                        inactive: {
                            opacity: 1
                        },
                    }
                })

                if (optionsController.options.showErrors) 
                {
                    options.series.push({
                        name: "Bin Content Error",
                        type: "errorbar",
                        data: yValues[i].map(function(value, index) {
                            return [value - yErr[i][index], value + yErr[i][index]]
                        }),
                        marker: {
                            radius: 3
                        },
                        tooltip: {
                            headerFormat: "",
                            pointFormat: '<b>{point.series.name}</b><br> <b>Run No:</b> {point.category}<br/><b>Error Range</b> : {point.low} to {point.high}<br/>'
                        },
                        animation: false,
                        point: {
                            events: {
                                click: () => false
                            }
                        },
                    })
                }
            }
            
            if (optionsController.options.showDurations)
            {
                options.series.push({
                    type: "column",
                    name: "Run Duration",
                    yAxis: 1,
                    borderRadius: 2,
                    color: "rgba(191, 191, 191, 0.9)",
                    zIndex: -1,
                    groupPadding: 0,
                    pointPadding: 0,
                    borderWidth: 0,
                    tooltip: {
                        headerFormat: "",
                        pointFormat: '<b>Run No</b>: {point.category}<br/><b>Duration</b>: {point.y}<br/>'
                    },
                    data: durations,
                    animation: false,
                    states: {
                        inactive: {
                            opacity: 1
                        }
                    },
                    point: {
                        events: {
                            click: () => false
                        }
                    },
                })
            }
            
            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        drawXRangePlot: function(plotData, renderTo) 
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const durations = plotData.series[0].trends.map(x => x.oms_info.duration)
            const deliveredLumis = plotData.series[0].trends.map(x => parce_lumi(x.oms_info.delivered_lumi))
            const seriesTitles = plotData.series.map(x => x.metadata.plot_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]

            const bands = this.getXRangeFillBands(optionsController.options.showDeliveredLumi ? deliveredLumis : durations, fills)
            
            const options = {
                credits: {
                    enabled: false
                },
                chart: {
                    renderTo: renderTo,
                    zoomType: "xy",
                    animation: false
                },
                lang: {
                    noData: "No data found"
                },
                title: {
                    text: plotName,
                    useHTML: true
                },
                subtitle: {
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
                    useHTML: true
                },
                xAxis: {
                    title: {
                        text: "Run No.",
                    },
                    type: "linear",
                    labels: {
                        rotation: -45,
                    },
                },
                yAxis: [
                    {
                        title: {
                            text: yTitle,
                            useHTML: true
                        },
                        min: min_y,
                        max: max_y,
                    },
                ],
                legend: {
                    useHTML: true 
                },
                plotOptions: {
                    xrange: {
                        grouping: false,
                        borderRadius: 0,
                    },
                    series: {
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
                                    const plotBands = this.chart.xAxis[0].plotLinesAndBands;
                                    if (!this.visible) {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                        }
                                    }
                                    else {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                        }
                                    }
                                }
                            }
                        } : {},
                        allowPointSelect: true,
                        turboThreshold: 2000,
                        point: {
                            events: {
                                click: function () {
                                    const parent = $(this.series.chart.container).parent().parent()
                                    
                                    if(fullScreenController.isFullScreen) {
                                        fullScreenController.selectDataPoint(this.series_index, this.index)
                                    }
                                    else {
                                        main.updateLinks(parent, plotData, this.run, this.series_index)
                                    }
                                },
                                unselect: function () {
                                    // Disable deselection
                                    return false
                                }
                            }
                        },
                    }
                },
                series: optionsController.options.showFills ?
                    [{
                        name: "Fills",
                        color: this.plotBandColor,
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            for(let i = 0; i < plotData.series.length; i++)
            {
                 const tooltip = `
                    <b>Value:</b> {point.y_readable}<br>
                    <b>Error:</b> {point.error_readable}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Duration:</b> {point.duration_readable}<br/>
                    <b>Delivered luminosity:</b> {point.del_lumi_readable} <i>pb<sup>-1</sup></i><br/>
                    <b>Start time:</b> {point.start_time}<br/>
                    <b>End time:</b> {point.end_time}<br/>
                    Click on the data point to reveal more info.`

                const data = plotData.series[i].trends.map(trend => ({
                    y:                  trend.value,
                    error:              trend.error,
                    y_readable:         helpers.toExponential(trend.value, 2),
                    error_readable:     helpers.toExponential(trend.error, 2),
                    run:                trend.run,
                    del_lumi:           parce_lumi( trend.oms_info.delivered_lumi ),
                    duration:           trend.oms_info.duration,
                    series_index:       i,
                    duration_readable:  helpers.secondsToHHMMSS(trend.oms_info.duration),
                    del_lumi_readable:  helpers.toExponential(parce_lumi(trend.oms_info.delivered_lumi), 3),
                    start_time:         trend.oms_info.start_time,
                    end_time:           trend.oms_info.end_time
                }))

                const ticks = []

                for (let j = 0; j < data.length; j++) 
                {
                    let valueForBinLength = data[j].duration
                    if(optionsController.options.showDeliveredLumi)
                        valueForBinLength = data[j].del_lumi

                    // Make sure bin length is not 0
                    if(valueForBinLength === 0)
                        valueForBinLength = 1

                    const prev_x2 = get_prev_x2(j, data)
                    data[j].x = prev_x2
                    data[j].x2 = prev_x2 + valueForBinLength

                    ticks.push(prev_x2 + (data[j].dur / 2));
                    
                    function get_prev_x2(index, arr) {
                        return index === 0 ? 0 : arr[index - 1].x2;
                    }
                }

                Object.assign(options.xAxis, {
                    labels: {
                        enabled: true,
                        formatter: function () {
                            const index = ticks.indexOf(this.value);
                            const n = parseInt(ticks.length / 10);

                            // Show only every nth label and, always, the last one
                            if (index % n != 0 && index != ticks.length - 1)
                                return ""
            
                            return xValues[index];
                        },
                    },
                    tickPositions: ticks,
                    plotBands: optionsController.options.showFills ? bands : []
                })

                options.series.push({
                    name: seriesTitles[i],
                    type: "xrange",
                    pointWidth: 6,
                    data: data,
                    color: helpers.seriesColors[i],
                    colorByPoint: false,
                    tooltip: {
                        headerFormat: "",
                        pointFormat: tooltip,
                    },
                    showInLegend: true,
                    animation: false
                })

                if (optionsController.options.showErrors) 
                {
                    options.series.push({
                        type: "xrange",
                        pointWidth: 9,
                        data: yErr[i].map((element, index) => {
                            return {
                                x: data[index].x,
                                x2: data[index].x2,
                                y: data[index].y + element
                            }
                        }),
                        color: helpers.seriesColors[i],
                        colorByPoint: false,
                        showInLegend: false,
                        animation: false,
                        enableMouseTracking: false,
                        states: {
                            inactive: {
                                opacity: 1
                            }
                        },
                        point: {
                            events: {
                                click: () => false
                            }
                        },
                    })
            
                    options.series.push({
                        type: "xrange",
                        pointWidth: 9,
                        data: yErr[i].map((element, index) => {
                            return {
                                x: data[index].x,
                                x2: data[index].x2,
                                y: data[index].y - element
                            }
                        }),
                        color: helpers.seriesColors[i],
                        colorByPoint: false,
                        showInLegend: false,
                        animation: false,
                        enableMouseTracking: false,
                        states: {
                            inactive: {
                                opacity: 1
                            }
                        },
                        point: {
                            events: {
                                click: () => false
                            }
                        },
                    })
                }
            }

            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        drawXRangeDatetimePlot: function(plotData, renderTo)
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const times = plotData.series[0].trends.map(x => [x.oms_info.start_time, x.oms_info.end_time])
            const seriesTitles = plotData.series.map(x => x.metadata.plot_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]
            
            const options = {
                credits: {
                    enabled: false
                },
                chart: {
                    renderTo: renderTo,
                    type: "xrange",
                    zoomType: "xy",
                    animation: false
                },
                lang: {
                    noData: "No data found"
                },
                title: {
                    text: plotName,
                    useHTML: true
                },
                subtitle: {
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
                    useHTML: true
                },
                xAxis: {
                    title: {
                        text: "Run No.",
                    },
                    type: "datetime",
                    labels: {
                        rotation: -45,
                    },
                },
                yAxis: [
                    {
                        title: {
                            text: yTitle,
                            useHTML: true
                        },
                        min: min_y,
                        max: max_y,
                    },
                ],
                legend: {
                    useHTML: true 
                },
                plotOptions: {
                    xrange: {
                        grouping: false,
                        borderRadius: 0,
                    },
                    series: {
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
                                    const plotBands = this.chart.xAxis[0].plotLinesAndBands;
                                    if (!this.visible) {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                        }
                                    }
                                    else {
                                        for (let i = 0; i < plotBands.length; i++) {
                                            this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                            $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                        }
                                    }
                                }
                            }
                        } : {},
                        allowPointSelect: true,
                        turboThreshold: 2000,
                        point: {
                            events: {
                                click: function () {
                                    const parent = $(this.series.chart.container).parent().parent()

                                    if(fullScreenController.isFullScreen) {
                                        fullScreenController.selectDataPoint(this.series_index, this.index)
                                    }
                                    else {
                                        main.updateLinks(parent, plotData, this.run, this.series_index)
                                    }
                                },
                                unselect: function () {
                                    // Disable deselection
                                    return false
                                }
                            }
                        }
                    }
                },
                series: optionsController.options.showFills ?
                    [{
                        name: "Fills",
                        color: this.plotBandColor,
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            const bands = this.getXRangeDatetimeFillBands(fills, times)

            Object.assign(options.xAxis, {
                plotBands: optionsController.options.showFills ? bands : []
            })

            for(let i = 0; i < plotData.series.length; i++)
            {
                const tooltip = `
                    <b>Value:</b> {point.y_readable}<br>
                    <b>Error:</b> {point.error_readable}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Duration:</b> {point.duration_readable}<br/>
                    <b>Delivered luminosity:</b> {point.del_lumi} <i>pb<sup>-1</sup></i><br/>
                    <b>Start time:</b> {point.start_time}<br/>
                    <b>End time:</b> {point.end_time}<br/>
                    Click on the data point to reveal more info.`

                const data = plotData.series[i].trends.map(trend => ({
                    x:                  new Date(trend.oms_info.start_time).getTime(), 
                    x2:                 new Date(trend.oms_info.end_time).getTime(), 
                    y:                  trend.value,
                    error:              trend.error,
                    y_readable:         helpers.toExponential(trend.value, 2),
                    error_readable:     helpers.toExponential(trend.error, 2),
                    run:                trend.run,
                    series_index:       i,
                    duration_readable:  helpers.secondsToHHMMSS(trend.oms_info.duration),
                    del_lumi:           helpers.toExponential( parce_lumi(trend.oms_info.delivered_lumi), 3),
                    start_time:         trend.oms_info.start_time,
                    end_time:           trend.oms_info.end_time
                }))

                options.series.push({
                    name: seriesTitles[i],
                    type: "xrange",
                    pointWidth: 6,
                    data: data,
                    color: helpers.seriesColors[i],
                    colorByPoint: false,
                    tooltip: {
                        headerFormat: "",
                        pointFormat: tooltip
                    },
                    showInLegend: true,
                    animation: false
                })

                if (optionsController.options.showErrors) 
                {
                    options.series.push({
                        type: "xrange",
                        pointWidth: 9,
                        data: yErr[i].map((element, index) => {
                            return {
                                x: data[index].x,
                                x2: data[index].x2,
                                y: data[index].y + element
                            }
                        }),
                        color: helpers.seriesColors[i],
                        colorByPoint: false,
                        showInLegend: false,
                        animation: false,
                        enableMouseTracking: false,
                        states: {
                            inactive: {
                                opacity: 1
                            }
                        },
                        point: {
                            events: {
                                click: () => false
                            }
                        },
                    })
            
                    options.series.push({
                        type: "xrange",
                        pointWidth: 9,
                        data: yErr[i].map((element, index) => {
                            return {
                                x: data[index].x,
                                x2: data[index].x2,
                                y: data[index].y - element
                            }
                        }),
                        color: helpers.seriesColors[i],
                        colorByPoint: false,
                        showInLegend: false,
                        animation: false,
                        enableMouseTracking: false,
                        states: {
                            inactive: {
                                opacity: 1
                            }
                        },
                        point: {
                            events: {
                                click: () => false
                            }
                        },
                    })
                }
            }

            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        getScatterFillBands: function(xValues, fills)
        {
            const bands = []
            let start_i = 0
            let lastFill = 0
            let flag = false

            for (let i = 0; i < xValues.length; i++) 
            {
                if (fills[i] !== lastFill)
                {
                    if (flag) {
                        bands.push({
                            color: this.plotBandColor,
                            from: start_i - 0.5,
                            to: i - 1 + 0.5,
                            id: "fills"
                        });
                    }
                    else 
                        start_i = i;
                    
                    flag = !flag
                    lastFill = fills[i]
                }
            }

            // Add last fill if needed
            if (flag) 
            {
                bands.push({
                    color: this.plotBandColor,
                    from: start_i - 0.5,
                    to: xValues.length - 1 + 0.5,
                    id: "fills"
                })
            }

            return bands
        },

        getXRangeFillBands: function(durations, fills)
        {
            if(fills.length === 0 || durations.length === 0)
                return []

            // Group by fill and sum durations
            let bands = []
            let lastFill = fills[0]
            let durSum = 0
            let lastDurSum = 0;

            for(let j = 0; j < fills.length; j++)
            {
                if(fills[j] != lastFill)
                {
                    bands.push({color: this.plotBandColor, from: lastDurSum, to: durSum, id: "fills"})
                    lastDurSum = durSum
                    lastFill = fills[j]
                }

                durSum += durations[j]
            }
            
            // Add last fill
            bands.push({color: this.plotBandColor, from: lastDurSum, to: durSum, id: "fills"})

            // Remove every second
            bands = bands.filter(function(_, i) {
                return i % 2 === 0;
            })

            return bands
        },

        getXRangeDatetimeFillBands: function(fills, times)
        {
            if(fills.length === 0 || times.length === 0)
                return []
            
            times = times.map(x => x.map(x1 => new Date(x1).getTime()))

            const bands = []
            let lastFill = fills[0]
            let lastTime = times[0][0]

            for(let j = 0; j < fills.length - 1; j++)
            {
                if(fills[j] != lastFill)
                {
                    bands.push({color: this.plotBandColor, from: lastTime, to: times[j - 1][1], id: "fills"})
                    lastFill = fills[j]
                    lastTime = times[j][0]
                }
            }
            
            // Add last fill
            bands.push({color: this.plotBandColor, from: lastTime, to: times[times.length - 1][1], id: "fills"})

            return bands
        }
    }
}())
