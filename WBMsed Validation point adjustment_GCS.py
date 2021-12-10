"""
Before running the script you have to extract the modeled values from the STN network to the shapefile with points that you needed moved. Create a field called "Model_Area".

"""


import os
import time
import arcpy
import shutil
from arcpy import env

t0 = time.time()
print t0

Shapefile = "MnS9_05_HydroSTN30.shp"      #This has to have a GCS for the script to run
name_of_final_shpaefile = "MnS9_05_HydroSTN30_adjusted.shp"
HydroSTN_raw  = "Area_HydroSTN30_v3_06min.tif"        #This has to have a GCS for the script to run
path0 = "Z:\\WBMsed_Validation\\Sep2020\\"    #Put the "Area_HydroSTN30_06min.tif" and the layer that needs to be adjusted inside this folder. Your output will be created within this folder.
Buff_dist = "0.6 DecimalDegrees"   #This is the search radius of the current point. It searches pixels within this radius for an optimum location.
Latitude = 'Latitude'  #The name of the Latitude field in the layer to be adjusted (The current layer)
Longitude = 'Longitude'  #The name of the Longitude field in the layer to be adjusted (The current layer)
fieldName1 = "Long"   #The name of the Longitude field in the layer that will be adjusted
fieldName2 = "Lat"    #The name of the Latitude field in the layer that will be adjusted

field_name = 'FID'
field_name1 = 'Model_Area'    #What the model is predicting now based on the current location of point!
field_name2 = 'BasinArea'    #real area of catchment #This has to be a float! The same as Model_area!!!
field_name5 =  'Objectid'      #This is an identification number. Cna be a site number, ID anything of that sought!! Something unique other than the FID. #'Site_'



class LicenseError(Exception):
    pass
try:
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        raise LicenseError

    from arcpy.sa import *

    os.chdir(path0)
    env.workspace = path0
    arcpy.env.overwriteOutput = True


    arcpy.RasterToPoint_conversion(HydroSTN_raw, "Raster_points_GCS.shp", "VALUE")       # Cnoverts the Model Raster to points.
    print "Raster to Points Converted"

    #arcpy.Delete_management("Raster_points_lyr")
    arcpy.MakeFeatureLayer_management("Raster_points_GCS.shp", "Raster_points_lyr", "", "", "")
    arcpy.CreateThiessenPolygons_analysis("Raster_points_GCS.shp", "Theissen_pols_GCS.shp", "ONLY_FID")     # Create Thiessen Polygons using points.
    print "Thiessen Polygons Created"

    #Section 1
    SC1 = arcpy.SearchCursor(Shapefile)
    for row in SC1:

        FIDval = row.getValue(field_name)
        Modelval = row.getValue(field_name1)
        Catchment_area = row.getValue(field_name2)
        IDofDAM = row.getValue(field_name5)
        IDofDAM = int(IDofDAM)
        Difference = abs(Modelval-Catchment_area)
        print("FID:  {0} Dam ID:  {1}".format(FIDval, IDofDAM))


        arcpy.MakeFeatureLayer_management(Shapefile, "feature_layer")
        arcpy.SelectLayerByAttribute_management("feature_layer", "NEW_SELECTION", '"FID" IN ({})'.format(FIDval))
        arcpy.FeatureClassToFeatureClass_conversion("feature_layer", path0, "initial_" + str(FIDval) + ".shp")
        arcpy.Delete_management("feature_layer")
        arcpy.Buffer_analysis("initial_" + str(FIDval) + ".shp", "initial_buff_" + str(FIDval) + ".shp", Buff_dist, "FULL", "ROUND", "ALL", "", "PLANAR")

        # Use the thiessen polygons to find out which polygons intersect the buffer. Then, we use the rasterpoints layer (which are the centroids) of the modeled raster pixels - this should be written properly!!!
        arcpy.MakeFeatureLayer_management("Theissen_pols_GCS.shp", "theissen_lyr", "", "", "")
        arcpy.SelectLayerByLocation_management("theissen_lyr", "INTERSECT", "initial_buff_" + str(FIDval) + ".shp","", "NEW_SELECTION")
        arcpy.FeatureClassToFeatureClass_conversion("theissen_lyr", path0, "ovlap_thie_" + str(FIDval) + ".shp")
        arcpy.Delete_management("theissen_lyr")

        arcpy.SelectLayerByLocation_management("Raster_points_lyr", "COMPLETELY_WITHIN", "ovlap_thie_" + str(FIDval) + ".shp", "", "NEW_SELECTION")
        arcpy.FeatureClassToFeatureClass_conversion("Raster_points_lyr", path0, "Raster_points_" + str(FIDval) + ".shp")


        #Section 2
        inFeature = "Raster_points_" + str(FIDval) + ".shp"
        fieldType = "FLOAT"
        field_name11 = "Hydro_area"
        arcpy.AddField_management(inFeature, field_name11, fieldType)
        with arcpy.da.UpdateCursor(inFeature, field_name11) as cursor:
            for row in cursor:
                if row[0] == 0:
                    row[0] = Modelval
                cursor.updateRow(row)

        List0 = []
        SC2 = arcpy.SearchCursor(inFeature)
        for row in SC2:
            field_name3 = 'grid_code'
            gridval = row.getValue(field_name3)
            List0.append(gridval)
        print List0
        del SC2

        List1 = []
        for x in List0:
            Difference_to_Catch = abs(x-Catchment_area)
            List1.append(Difference_to_Catch)
        print List1
        print Difference

        min_in_list1 = min(List1)
        number_of_mins = List1.count(min_in_list1)
        print number_of_mins
        path1 = path0 + "\\Outputs\\if_mins_are_one"
        if not os.path.exists(path1):
            os.makedirs(path1)
        path2 = path0 + "\\Outputs\\if_mins_are_morethanone"
        if not os.path.exists(path2):
            os.makedirs(path2)
        path3 = path0 + "\\Outputs\\Final_Outputs"
        if not os.path.exists(path3):
            os.makedirs(path3)

        if Difference >  min_in_list1:
            if number_of_mins ==1:
                postition_min = List1.index(min_in_list1)
                grid_val_of_min = List0[postition_min]

                arcpy.MakeFeatureLayer_management(inFeature, "feature_layer")
                arcpy.SelectLayerByAttribute_management("feature_layer", "NEW_SELECTION", '"grid_code" > ({} - 0.0001) AND "grid_code" < ({} + 0.0001)'.format(grid_val_of_min,grid_val_of_min))
                arcpy.FeatureClassToFeatureClass_conversion("feature_layer", path1, "finalrasterpoint_" + str(FIDval) + ".shp")
                arcpy.Delete_management("feature_layer")

                arcpy.MakeFeatureLayer_management(path1+"\\finalrasterpoint_" + str(FIDval) + ".shp", "feature_layer")
                arcpy.MakeFeatureLayer_management("initial_" + str(FIDval) + ".shp", "feature_layer_ini")

                ## You don't include 3 fields in the list of fields: Shape, Latitude field and Longitude Field. the one immediately below was for NWIS  sites. The one below that is for a version of MnS validation sites. You need to include USGS if you are running this script with USGS sites.
                #NWIS sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                          #field_name1, ['FID', 'Site_', 'Area_km2', 'SYear', 'EYear', 'NumDays', 'Qavr_cms', 'Qsavr_kgs', 'Qp2', 'sumQs2', 'sumQs_gtQp', 'Qs_prop2', 'Q_prop2', 'Days_prop2', 'Qp5', 'sumQs5', 'sumQs_gt_1', 'Qs_prop5', 'Q_prop5', 'Days_prop5', 'Qp10', 'sumQs10', 'sumQs_gt_2', 'Qs_prop10', 'Q_prop10', 'Days_prop1', 'Qp25', 'sumQs25', 'sumQs_gt_3', 'Qs_prop25', 'Q_prop25', 'Days_pro_1', 'Qp50', 'sumQs50', 'sumQs_gt_4', 'Qs_prop50', 'Q_prop50', 'Days_pro_2', 'Qp100', 'sumQs100', 'sumQs_gt_5', 'Qs_prop100', 'Q_prop100', 'Days_pro_3', 'Qp200', 'sumQs200', 'sumQs_gt_6', 'Qs_prop200', 'Q_prop200', 'Days_pro_4', 'Model_area'])
                #A version of MnS sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           #field_name1,
                                                           #['FID', 'FID_', 'River', 'Name', 'BasinArea', 'GlacierAre', 'Glaciers', 'Geology', 'Te', 'anthro', 'Tf', 'Temp', 'Area_km2', 'Relief_km', 'ObsQs_kgs', 'Mtyr_Obs', 'obsQ_m3s', 'Q_km3y', 'RegART', 'GLOB_ART', 'BQART_kgs', 'BQART_MTy', 'BQART', 'NewLitholo', 'OrigLithol', 'Area_km21', 'discharge_', 'discharge1', 'discharg_1', 'discharg_2', 'discharg_3', 'discharg_4', 'discharg_5', 'discharg_6', 'discharg_7', 'discharg_8', 'discharg_9', 'dischar_10', 'dischar_11', 'dischar_12', 'dischar_13', 'dischar_14', 'dischar_15', 'dischar_16', 'dischar_17', 'dischar_18', 'dischar_19', 'dischar_20', 'dischar_21', 'dischar_22', 'dischar_23', 'dischar_24', 'dischar_25', 'dischar_26', 'dischar_27', 'dischar_28', 'dischar_29', 'dischar_30', 'dischar_31', 'dischar_32', 'dischar_33', 'dischar_34', 'dischar_35', 'dischar_36', 'dischar_37', 'dischar_38', 'dischar_39', 'dischar_40', 'dischar_41', 'dischar_42', 'dischar_43', 'dischar_44', 'dischar_45', 'dischar_46', 'dischar_47', 'dischar_48', 'dischar_49', 'dischar_50', 'dischar_51', 'dischar_52', 'dischar_53', 'dischar_54', 'SedimentFl', 'Sediment_1', 'Sediment_2', 'Sediment_3', 'Sediment_4', 'Sediment_5', 'Sediment_6', 'Sediment_7', 'Sediment_8', 'Sediment_9', 'Sedimen_10', 'Sedimen_11', 'Sedimen_12', 'Sedimen_13', 'Sedimen_14', 'Sedimen_15', 'Sedimen_16', 'Sedimen_17', 'Sedimen_18', 'Sedimen_19', 'Sedimen_20', 'Sedimen_21', 'Sedimen_22', 'Sedimen_23', 'Sedimen_24', 'Sedimen_25', 'Sedimen_26', 'Sedimen_27', 'Sedimen_28', 'Sedimen_29', 'Sedimen_30', 'Sedimen_31', 'Sedimen_32', 'Sedimen_33', 'Sedimen_34', 'Sedimen_35', 'Sedimen_36', 'Sedimen_37', 'Sedimen_38', 'Sedimen_39', 'Sedimen_40', 'Sedimen_41', 'Sedimen_42', 'Sedimen_43', 'Sedimen_44', 'Sedimen_45', 'Sedimen_46', 'Sedimen_47', 'Sedimen_48', 'Sedimen_49', 'Sedimen_50', 'Sedimen_51', 'Sedimen_52', 'Sedimen_53', 'Sedimen_54', 'Sedimen_55', 'GFDLSed', 'IPSLSed', 'NorESMSed', 'GFDLDis', 'MIROCDis', 'MIROCSed', 'HadGEMSed', 'HadGEMDis', 'IPSLDis', 'NorESMDis', 'Dis_198020', 'NewDis_80_', 'Sed_198020', 'newsed_80_', 'Model_Area', 'Old_MnS'])
                #Bedload observation sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           #field_name1,['FID', 'Name', 'Area', 'ObsQ', 'ObsBedload', 'ObsSlope', 'Source', 'Area_Model', 'Area_bias', 'Model_BL', 'Model_Q201', 'Q80_10', 'BL_80_10', 'GloRS2p0', 'Bedload_V1', 'Qs_V1', 'Q_V1', 'Qbl_nVar', 'velocity', 'width9p3', 'Area_mod_1', 'Discharge', 'Global_Riv', 'W_temp', 'Sed_Conc', 'Syv_StWden', 'Bag_Dyn', 'Syv_StSlop', 'Syv_StDsWd', 'Syv_StDs', 'Syv_Dyn', 'Lam_StWden', 'Lam_StDsWd', 'Lam_StDs', 'Lam_Dyn', 'Bag_StWden', 'Bag_StDs', 'Bag_StSlop', 'Syv_StWd_1', 'Lam_StSlop', 'RiverSlope', 'Bedload_Sy', 'Bedload_Ba', 'Bedload_La', 'Discharg_1', 'Sus_Bag', 'Sus_Lam', 'Syvitaki', 'Lammers', 'Bagnold', 'Q', 'Model_Area', 'ObjectID'])

                # Version_2 of MnS
                joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           field_name1, ['FID', 'Objectid', 'River', 'Name', 'BasinArea', 'GlacierAre', 'Glaciers', 'Geology', 'Te', 'anthro', 'Tf', 'Temp', 'Area_km2', 'Relief_km', 'ObsQs_kgs', 'Mtyr_Obs', 'obsQ_m3s', 'Q_km3y', 'RegART', 'GLOB_ART', 'BQART_kgs', 'BQART_MTy', 'BQART', 'NewLitholo', 'OrigLithol', 'NewL_Qsbar', 'OrigL_Qsba', 'L_diff', 'OBJECTID_1', 'Area_Hydro', 'ar_dif', 'Area_Hyd_2', 'ar_dif_new', 'Area_Hyd_1', 'ar_dif_2', 'RASTERVALU', 'Ratio_Basi', 'Qs_FixPs_1', 'Q_FixPsi_1', 'Qsbar2000', 'Qs9p3_00_1', 'Area_Mod_1', 'Qs_NewMode', 'Qs_nGeom_1', 'Q_nGeom_1', 'qs_bar_nGe', 'Qs_nGeo_di', 'Q_nGeo_dis', 'FRR_SOD_WB', 'BQART_Te_2', 'Sed_Dist', 'Sed_Lin', 'Area_Hyd_3', 'Q_TrapInpu', 'Qs_TrapInp', 'Q_TrapIn_1', 'Qs_TrapI_2', 'Model_Area'])

                #USGS sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           #field_name1,['FID', 'OBJECTID', 'Site_','Area_km2', 'SYear', 'EYear', 'NumDays', 'Qavr_cms', 'Qsavr_kgs', 'Qp2', 'sumQs2', 'sumQs_gtQp', 'Qs_prop2', 'Q_prop2', 'Days_prop2', 'Qp5', 'sumQs5', 'sumQs_gt_1', 'Qs_prop5', 'Q_prop5', 'Days_prop5', 'Qp10', 'sumQs10', 'sumQs_gt_2', 'Qs_prop10', 'Q_prop10', 'Days_prop1', 'Qp25', 'sumQs25', 'sumQs_gt_3', 'Qs_prop25', 'Q_prop25', 'Days_pro_1', 'Qp50', 'sumQs50', 'sumQs_gt_4', 'Qs_prop50', 'Q_prop50', 'Days_pro_2', 'Qp100', 'sumQs100', 'sumQs_gt_5', 'Qs_prop100', 'Q_prop100', 'Days_pro_3', 'Qp200', 'sumQs200', 'sumQs_gt_6', 'Qs_prop200', 'Q_prop200', 'Days_pro_4', 'Area', 'RASTERVALU', 'area_ratio', 'aREA2', 'Qs_bar2016', 'Area_model', 'Q_model', 'Qb_model', 'Qs_model', 'Qs1980_203', 'Sed_diff', 'FRR_SOD__1', 'BQART_Te_3', 'Sed_Dist_1', 'Sed_Lin_1', 'Area_Hyd_4', 'Q_TrapInpu', 'Qs_TrapInp', 'Q_TrapInp', 'Qs_TrapI_1', 'Model_Area'])


                arcpy.CopyFeatures_management(joined_layers, path3 + "\\Dam_" + str(IDofDAM ) + ".shp")
                arcpy.Delete_management("feature_layer")
                arcpy.Delete_management("feature_layer_ini")

                arcpy.DeleteField_management(path3 + "\\Dam_" + str(IDofDAM ) + ".shp", ["pointid", "grid_code", "Hydro_area"])


            if number_of_mins > 1:
                postition_min = List1.index(min_in_list1)
                grid_val_of_min = List0[postition_min]

                arcpy.MakeFeatureLayer_management(inFeature, "feature_layer_1")
                arcpy.SelectLayerByAttribute_management("feature_layer_1", "NEW_SELECTION", '"grid_code" > ({} - 0.0001) AND "grid_code" < ({} + 0.0001)'.format(grid_val_of_min, grid_val_of_min))
                arcpy.FeatureClassToFeatureClass_conversion("feature_layer_1", path2, "finalrasterpoint_more_" + str(FIDval) + ".shp")
                arcpy.Delete_management("feature_layer_1")

                arcpy.Copy_management("initial_" + str(FIDval) + ".shp", "initial_copy_" + str(FIDval) + ".shp")
                arcpy.Near_analysis("initial_copy_" + str(FIDval) + ".shp", path2+"\\finalrasterpoint_more_" + str(FIDval) + ".shp")

                SC3 = arcpy.SearchCursor("initial_copy_" + str(FIDval) + ".shp")
                for row in SC3:
                    field_name4 = 'NEAR_FID'
                    FIDval_NEAR = row.getValue(field_name4)
                del SC3
                arcpy.MakeFeatureLayer_management(path2+"\\finalrasterpoint_more_" + str(FIDval) + ".shp", "feature_layer")
                arcpy.SelectLayerByAttribute_management("feature_layer", "NEW_SELECTION", '"FID" IN ({})'.format(FIDval_NEAR))
                arcpy.FeatureClassToFeatureClass_conversion("feature_layer", path2, "finalrasterpoint_morethan2_" + str(FIDval) + ".shp")
                arcpy.Delete_management("feature_layer")
                arcpy.Delete_management(path2+"\\finalrasterpoint_more_" + str(FIDval) + ".shp")

                arcpy.MakeFeatureLayer_management(path2+"\\finalrasterpoint_morethan2_" + str(FIDval) + ".shp", "feature_layer")
                arcpy.MakeFeatureLayer_management("initial_" + str(FIDval) + ".shp", "feature_layer_ini")

                ## NWIS first, a version of MnS below that, Bedload observation sites below that, USGS not here! You don't include 3 fields in the list of fields: Shape, Latitude field and Longitude Field.
                #NWIS sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini", field_name1, ['FID', 'Site_', 'Area_km2', 'SYear', 'EYear', 'NumDays', 'Qavr_cms', 'Qsavr_kgs', 'Qp2', 'sumQs2', 'sumQs_gtQp', 'Qs_prop2', 'Q_prop2', 'Days_prop2', 'Qp5', 'sumQs5', 'sumQs_gt_1', 'Qs_prop5', 'Q_prop5', 'Days_prop5', 'Qp10', 'sumQs10', 'sumQs_gt_2', 'Qs_prop10', 'Q_prop10', 'Days_prop1', 'Qp25', 'sumQs25', 'sumQs_gt_3', 'Qs_prop25', 'Q_prop25', 'Days_pro_1', 'Qp50', 'sumQs50', 'sumQs_gt_4', 'Qs_prop50', 'Q_prop50', 'Days_pro_2', 'Qp100', 'sumQs100', 'sumQs_gt_5', 'Qs_prop100', 'Q_prop100', 'Days_pro_3', 'Qp200', 'sumQs200', 'sumQs_gt_6', 'Qs_prop200', 'Q_prop200', 'Days_pro_4', 'Model_area'])

                """
                #Version of MnS (The fields change base on what is done to them outside this scipt!)
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           #field_name1,
                                                           #['FID', 'FID_', 'River', 'Name', 'BasinArea', 'GlacierAre', 'Glaciers', 'Geology', 'Te', 'anthro', 'Tf',
                 'Temp', 'Area_km2', 'Relief_km', 'ObsQs_kgs', 'Mtyr_Obs', 'obsQ_m3s', 'Q_km3y', 'RegART', 'GLOB_ART',
                 'BQART_kgs', 'BQART_MTy', 'BQART', 'NewLitholo', 'OrigLithol', 'Area_km21', 'discharge_', 'discharge1',
                 'discharg_1', 'discharg_2', 'discharg_3', 'discharg_4', 'discharg_5', 'discharg_6', 'discharg_7',
                 'discharg_8', 'discharg_9', 'dischar_10', 'dischar_11', 'dischar_12', 'dischar_13', 'dischar_14',
                 'dischar_15', 'dischar_16', 'dischar_17', 'dischar_18', 'dischar_19', 'dischar_20', 'dischar_21',
                 'dischar_22', 'dischar_23', 'dischar_24', 'dischar_25', 'dischar_26', 'dischar_27', 'dischar_28',
                 'dischar_29', 'dischar_30', 'dischar_31', 'dischar_32', 'dischar_33', 'dischar_34', 'dischar_35',
                 'dischar_36', 'dischar_37', 'dischar_38', 'dischar_39', 'dischar_40', 'dischar_41', 'dischar_42',
                 'dischar_43', 'dischar_44', 'dischar_45', 'dischar_46', 'dischar_47', 'dischar_48', 'dischar_49',
                 'dischar_50', 'dischar_51', 'dischar_52', 'dischar_53', 'dischar_54', 'SedimentFl', 'Sediment_1',
                 'Sediment_2', 'Sediment_3', 'Sediment_4', 'Sediment_5', 'Sediment_6', 'Sediment_7', 'Sediment_8',
                 'Sediment_9', 'Sedimen_10', 'Sedimen_11', 'Sedimen_12', 'Sedimen_13', 'Sedimen_14', 'Sedimen_15',
                 'Sedimen_16', 'Sedimen_17', 'Sedimen_18', 'Sedimen_19', 'Sedimen_20', 'Sedimen_21', 'Sedimen_22',
                 'Sedimen_23', 'Sedimen_24', 'Sedimen_25', 'Sedimen_26', 'Sedimen_27', 'Sedimen_28', 'Sedimen_29',
                 'Sedimen_30', 'Sedimen_31', 'Sedimen_32', 'Sedimen_33', 'Sedimen_34', 'Sedimen_35', 'Sedimen_36',
                 'Sedimen_37', 'Sedimen_38', 'Sedimen_39', 'Sedimen_40', 'Sedimen_41', 'Sedimen_42', 'Sedimen_43',
                 'Sedimen_44', 'Sedimen_45', 'Sedimen_46', 'Sedimen_47', 'Sedimen_48', 'Sedimen_49', 'Sedimen_50',
                 'Sedimen_51', 'Sedimen_52', 'Sedimen_53', 'Sedimen_54', 'Sedimen_55', 'GFDLSed', 'IPSLSed',
                 'NorESMSed', 'GFDLDis', 'MIROCDis', 'MIROCSed', 'HadGEMSed', 'HadGEMDis', 'IPSLDis', 'NorESMDis',
                 'Dis_198020', 'NewDis_80_', 'Sed_198020', 'newsed_80_', 'Model_Area', 'Old_MnS'])
                """

                #Bedload observation sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                           #field_name1, ['FID', 'Name', 'Area', 'ObsQ', 'ObsBedload', 'ObsSlope', 'Source', 'Area_Model', 'Area_bias', 'Model_BL', 'Model_Q201', 'Q80_10', 'BL_80_10', 'GloRS2p0', 'Bedload_V1', 'Qs_V1', 'Q_V1', 'Qbl_nVar', 'velocity', 'width9p3', 'Area_mod_1', 'Discharge', 'Global_Riv', 'W_temp', 'Sed_Conc', 'Syv_StWden', 'Bag_Dyn', 'Syv_StSlop', 'Syv_StDsWd', 'Syv_StDs', 'Syv_Dyn', 'Lam_StWden', 'Lam_StDsWd', 'Lam_StDs', 'Lam_Dyn', 'Bag_StWden', 'Bag_StDs', 'Bag_StSlop', 'Syv_StWd_1', 'Lam_StSlop', 'RiverSlope', 'Bedload_Sy', 'Bedload_Ba', 'Bedload_La', 'Discharg_1', 'Sus_Bag', 'Sus_Lam', 'Syvitaki', 'Lammers', 'Bagnold', 'Q', 'Model_Area', 'ObjectID'])

                #Version_2 of MnS
                joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini", field_name1,
                                                            ['FID', 'Objectid', 'River', 'Name', 'BasinArea', 'GlacierAre', 'Glaciers', 'Geology', 'Te', 'anthro', 'Tf', 'Temp', 'Area_km2', 'Relief_km', 'ObsQs_kgs', 'Mtyr_Obs', 'obsQ_m3s', 'Q_km3y', 'RegART', 'GLOB_ART', 'BQART_kgs', 'BQART_MTy', 'BQART', 'NewLitholo', 'OrigLithol', 'NewL_Qsbar', 'OrigL_Qsba', 'L_diff', 'OBJECTID_1', 'Area_Hydro', 'ar_dif', 'Area_Hyd_2', 'ar_dif_new', 'Area_Hyd_1', 'ar_dif_2', 'RASTERVALU', 'Ratio_Basi', 'Qs_FixPs_1', 'Q_FixPsi_1', 'Qsbar2000', 'Qs9p3_00_1', 'Area_Mod_1', 'Qs_NewMode', 'Qs_nGeom_1', 'Q_nGeom_1', 'qs_bar_nGe', 'Qs_nGeo_di', 'Q_nGeo_dis', 'FRR_SOD_WB', 'BQART_Te_2', 'Sed_Dist', 'Sed_Lin', 'Area_Hyd_3', 'Q_TrapInpu', 'Qs_TrapInp', 'Q_TrapIn_1', 'Qs_TrapI_2', 'Model_Area'])

                #USGS sites
                #joined_layers = arcpy.JoinField_management("feature_layer", field_name11, "feature_layer_ini",
                                                            #field_name1,['FID', 'OBJECTID', 'Site_','Area_km2', 'SYear', 'EYear', 'NumDays', 'Qavr_cms', 'Qsavr_kgs', 'Qp2', 'sumQs2', 'sumQs_gtQp', 'Qs_prop2', 'Q_prop2', 'Days_prop2', 'Qp5', 'sumQs5', 'sumQs_gt_1', 'Qs_prop5', 'Q_prop5', 'Days_prop5', 'Qp10', 'sumQs10', 'sumQs_gt_2', 'Qs_prop10', 'Q_prop10', 'Days_prop1', 'Qp25', 'sumQs25', 'sumQs_gt_3', 'Qs_prop25', 'Q_prop25', 'Days_pro_1', 'Qp50', 'sumQs50', 'sumQs_gt_4', 'Qs_prop50', 'Q_prop50', 'Days_pro_2', 'Qp100', 'sumQs100', 'sumQs_gt_5', 'Qs_prop100', 'Q_prop100', 'Days_pro_3', 'Qp200', 'sumQs200', 'sumQs_gt_6', 'Qs_prop200', 'Q_prop200', 'Days_pro_4', 'Area', 'RASTERVALU', 'area_ratio', 'aREA2', 'Qs_bar2016', 'Area_model', 'Q_model', 'Qb_model', 'Qs_model', 'Qs1980_203', 'Sed_diff', 'FRR_SOD__1', 'BQART_Te_3', 'Sed_Dist_1', 'Sed_Lin_1', 'Area_Hyd_4', 'Q_TrapInpu', 'Qs_TrapInp', 'Q_TrapInp', 'Qs_TrapI_1', 'Model_Area'])

                arcpy.CopyFeatures_management(joined_layers, path3 + "\\Dam_" + str(IDofDAM ) + ".shp")
                arcpy.Delete_management("feature_layer")
                arcpy.Delete_management("feature_layer_ini")

                arcpy.DeleteField_management(path3 + "\\Dam_" + str(IDofDAM) + ".shp", ["pointid", "grid_code","Hydro_area"])
                arcpy.Delete_management("initial_copy_" + str(FIDval) + ".shp")

        if Difference <=  min_in_list1:
            arcpy.Copy_management("initial_" + str(FIDval) + ".shp", path3+"\\Dam_" + str(IDofDAM ) + ".shp")
            arcpy.DeleteField_management(path3+"\\Dam_" + str(IDofDAM ) + ".shp", [Latitude, Longitude])

        arcpy.Delete_management("initial_" + str(FIDval) + ".shp")
        arcpy.Delete_management("Raster_points_" + str(FIDval) + ".shp")
        arcpy.Delete_management("ovlap_thie_" + str(FIDval) + ".shp")
        arcpy.Delete_management("initial_buff_" + str(FIDval) + ".shp")
        print "Nmber of Dams Completed:  {}".format(int(FIDval) + 1)

    del SC1

    env.workspace = path3
    shplist1 = arcpy.ListFeatureClasses('*.shp')
    arcpy.Merge_management(shplist1, path0 + "\\"+name_of_final_shpaefile)
    env.workspace = path0

    inFeature = name_of_final_shpaefile

    fieldType = "DOUBLE"
    arcpy.AddField_management(inFeature, fieldName1, fieldType)
    arcpy.AddField_management(inFeature, fieldName2, fieldType)
    expression1 = "{0}".format("!SHAPE.extent.XMax!")
    expression2 = "{0}".format("!SHAPE.extent.YMax!")
    arcpy.CalculateField_management(inFeature, fieldName1, expression1, "PYTHON_9.3")
    arcpy.CalculateField_management(inFeature, fieldName2, expression2, "PYTHON_9.3")

    ExtractMultiValuesToPoints(name_of_final_shpaefile, [[HydroSTN_raw, "New_Model_Area"]], "NONE")
    shutil.rmtree(path0 + "\\Outputs")


    arcpy.CheckInExtension("Spatial")
except LicenseError:
    print("Spatial Analyst license is unavailable")

print 'done'
t1 = time.time()

total = t1 -t0
print total

