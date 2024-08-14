

# define the types of data formats or measurements for your viewer 
# the highest level key is the viewer endpoint name
# the value is a dictionary specifying the filter criteria
# its only possible to filter on measurement or data_format at this time

viewer_data_format_map = {
                        "hyperspectra_viewer":  {
                            "measurement":"hyperspec_picam_mcl"
                        },
                        "powerfit_viewer": {
                            "measurement":"picam_readout"
                        },
                        "dvs_viewer": {
                            "data_format":'xls'
                        }
                    }