
const seriesListComponent = (function() {
    return {
        dataIndexLoaded: false,
        maxId: 0,
        series: [],

        enterFullScreen: async function()
        {
            if(!this.dataIndexLoaded)
            {
                try {
                    const base = config.getBaseAPIUrl()
                    const response = await fetch(`${base}/plot_selection`, {
                        credentials: "same-origin"
                    })
                    const plotDataIndex = await response.json()

                    selectComponent.register(
                        ['#fs-subsystem-select', '#fs-pd-select', '#fs-processing-string-select', '#fs-plot-select'], 
                        plotDataIndex, 
                        ['Select a subsystem', 'Select a primary dataset', 'Select a processing string', 'Select a plot'])
                    
                    this.dataIndexLoaded = true
                }
                catch(error) {
                    console.error(error)
                }
            }
            
            $("#fs-subsystem-select").val(selectionController.selectedSubsystem()).trigger('change')
            $("#fs-pd-select").val(selectionController.selectedPD()).trigger('change')
            $("#fs-processing-string-select").val(selectionController.selectedProcessingString()).trigger('change')
        },

        setup: function(series, correlation) {
            this.maxId = 0
            this.series = []

            $("#fs-series-list-container").empty()
            series.forEach(element => {
                this.addNewSeries(selectionController.selectedSubsystem(), selectionController.selectedPD(), selectionController.selectedProcessingString(), element.metadata.plot_title)
            })

            if(correlation) {
                $("#fs-correlation-checkbox").prop("checked", true)
            }
        },

        addNewSeries: async function(subsystem, pd, ps, name, animated = false, series_id = undefined) {
            const id = subsystem + pd + ps + name

            // Check if this series does not exist yet
            if(this.series.filter(x => x.id === id && x.removed === false).length > 0)
                return

            // Add series to the plot
            if(series_id !== undefined)
            {
                const runFrom = fullScreenController.plotData.series[0].trends[0].run
                const runTo = fullScreenController.plotData.series[0].trends[fullScreenController.plotData.series[0].trends.length - 1].run

                let allSeries = []
                try {
                    this.showSpinner()
                    const base = config.getBaseAPIUrl()
                    const url = `${base}/data?trend_id=${series_id}&from_run=${runFrom}&to_run=${runTo}&subsystem=${subsystem}&pd=${pd}&processing_string=${ps}`
                    const response = await fetch(url, {
                        credentials: "same-origin"
                    })
                    allSeries = await response.json()
                }
                catch(error) {
                    console.error(error)
                    this.showError("Unable to get the series data from the API")
                    return
                }
                finally {
                    this.hideSpinner()
                }

                if(allSeries.length == 0)
                {
                    this.showError("The selected series doesn't exist for the selected runs")
                    return
                }
            
                fullScreenController.plotData.series.push(allSeries[0])
                await fullScreenController.redrawPlot()
            }

            // Add series to a list in this component
            const index = this.maxId++
            this.series[index] = {
                id: id,
                subsystem: subsystem,
                pd: pd,
                processing_string: ps,
                name: name,
                removed: false,
            }

            $("#fs-series-list-container").append(`
            <li class="list-group-item" id="fs-series-list-item-${index}">
				<div class="row">
					<div class="col mb-0">
						<small>${subsystem}/${pd}/${ps}</small></br>
						${name}
					</div>
					<div class="col-auto pr-1 mt-auto mb-auto">
						<button class="btn btn-sm btn-outline-danger" onclick="seriesListComponent.removeClicked(${index})">Remove</button>
					</div>
				</div>
			</li>
            `)

            if(animated === true) 
            {
                $(`#fs-series-list-item-${index}`).hide(0)
                $(`#fs-series-list-item-${index}`).slideDown("fast")
            }

            this.toggleCorrelationCheckboxIfNeeded()
            this.hideError()
        },

        removeSeries: async function(index) {
            // We can't remove last trend
            if(fullScreenController.plotData.series.length == 1)
                return
            
            // Remove from plot data that will be used to redraw the plot
            const toRemoveIndex = fullScreenController.plotData.series.findIndex(x => {
                return x.metadata.subsystem === this.series[index].subsystem && 
                       x.metadata.pd === this.series[index].pd &&
                       x.metadata.processing_string === this.series[index].processing_string &&
                       x.metadata.name === this.series[index].name
            })

            if (toRemoveIndex > -1)
                fullScreenController.plotData.series.splice(toRemoveIndex, 1)

            await fullScreenController.redrawPlot()
            
            // Update UI
            const target = $(`#fs-series-list-item-${index}`)
            target.slideUp("fast", function() { 
                target.remove() 
            })

            this.series[index].removed = true
            this.toggleCorrelationCheckboxIfNeeded()
        },

        toggleCorrelationCheckboxIfNeeded: function() {
            const initialState = $("#fs-correlation-checkbox").prop("checked")
            const seriesLength = this.series.filter(x => x.removed === false).length
            if(seriesLength === 2 || seriesLength === 3)
            {
                $("#fs-correlation-checkbox").prop("disabled", false)
            }
            else
            {
                $("#fs-correlation-checkbox").prop("disabled", true)
                $("#fs-correlation-checkbox").prop("checked", false)

                // Transmit event only if value actually changed
                if(initialState == true) {
                    $('#fs-correlation-checkbox').trigger('change')
                }
            }
        },

        addClicked: async function () {
            // Check if value is selected
            if(!$("#fs-plot-select option:selected").is("[disabled]"))
            {
                await this.addNewSeries($("#fs-subsystem-select").val(), $("#fs-pd-select").val(), 
                    $("#fs-processing-string-select").val(), $("#fs-plot-select option:selected").text(), 
                    true, parseInt($("#fs-plot-select option:selected").val()))
            }
        },

        addOMSTrendClicked: async function () {
            const selected_trend_id = $("#fs-oms-trend-select").val()
            const plotTitle = $("#fs-oms-trend-select option:selected").text()

            const id = `oms_trend_${selected_trend_id}`

            // Check if this series does not exist yet
            if(this.series.filter(x => x.id === id && x.removed === false).length > 0)
                return

            // Add series to the plot
            const omsTrend = { 
                metadata: {
                    name: plotTitle,
                    plot_title: plotTitle,
                    subsystem: fullScreenController.plotData.series[0].metadata.subsystem,
                    y_title: "Units of the OMS value",
                },
                trends: []
            }

            fullScreenController.plotData.series[0].trends.forEach(element => {
                let value = 0
                if(selected_trend_id == 0)
                    value = element.oms_info.duration
                else if(selected_trend_id == 1)
                    value = parce_lumi( element.oms_info.delivered_lumi )
                else if(selected_trend_id == 2)
                    value = parce_lumi( element.oms_info.recorded_lumi )
                else if(selected_trend_id == 3)
                    value = parce_lumi( element.oms_info.end_lumi )
                else if(selected_trend_id == 4)
                    value = element.oms_info.b_field
                else if(selected_trend_id == 5)
                    value = element.oms_info.energy
                else if(selected_trend_id == 6)
                    value = element.oms_info.hlt_physics_rate
                else if(selected_trend_id == 7)
                    value = element.oms_info.l1_rate

                omsTrend.trends.push({
                    run: element.run,
                    lumi: 0,
                    value: value,
                    error: 0,
                    oms_info: element.oms_info,
                    id: 0
                })
            })

            fullScreenController.plotData.series.push(omsTrend)
            await fullScreenController.redrawPlot()

            // Add series to a list in this component
            const index = this.maxId++
            this.series[index] = {
                id: id,
                subsystem: fullScreenController.plotData.series[0].metadata.subsystem,
                pd: undefined,
                processing_string: undefined,
                name: plotTitle,
                removed: false,
            }

            $("#fs-series-list-container").append(`
            <li class="list-group-item" id="fs-series-list-item-${index}">
				<div class="row">
					<div class="col mb-0">
						<small>OMS value</small></br>
						${plotTitle}
					</div>
					<div class="col-auto pr-1 mt-auto mb-auto">
						<button class="btn btn-sm btn-outline-danger" onclick="seriesListComponent.removeClicked(${index})">Remove</button>
					</div>
				</div>
			</li>
            `)

            $(`#fs-series-list-item-${index}`).hide(0)
            $(`#fs-series-list-item-${index}`).slideDown("fast")

            this.toggleCorrelationCheckboxIfNeeded()
            this.hideError()
        },

        removeClicked: function (index) {
            this.removeSeries(index)
        },

        showError: function(error) {
            $("#fs-add-series-error").text(error)
            $("#fs-add-series-error").slideDown()
        },

        hideError: function() {
            $("#fs-add-series-error").slideUp()
        },

        showSpinner: function() {
            $("#fs-add-series-button-spinner").show()
            $("#fs-add-series-button-text").hide()
        },

        hideSpinner: function() {
            $("#fs-add-series-button-spinner").hide()
            $("#fs-add-series-button-text").show()
        },

        documentReady: function() {
            $('#fs-series-collapse').on('show.bs.collapse', function () {
                $("#fs-series-collapse-show-icon").hide()
                $("#fs-series-collapse-hide-icon").show()
            })

            $('#fs-series-collapse').on('hide.bs.collapse', function () {
                $("#fs-series-collapse-show-icon").show()
                $("#fs-series-collapse-hide-icon").hide()
            })

            $('#fs-correlation-checkbox').change(async function() {
                if(fullScreenController.plotData.correlation !== this.checked)
                {
                    fullScreenController.plotData.correlation = this.checked
                    await fullScreenController.redrawPlot()
                }
            });
        }
    }
}())
