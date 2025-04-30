import json
from lxml import etree
from datetime import datetime

# Load input data
with open("laboratory.txt", "r", encoding="utf-8") as f:
    laboratory_data = json.load(f)

with open("code_comparison.txt", "r", encoding="utf-8") as f:
    code_comparison_data = json.load(f)

with open("comparison_data.txt", "r", encoding="utf-8") as f:
    comparison_results = json.load(f)

with open("comparison_board.txt", "r", encoding="utf-8") as f:
    board_data = json.load(f)

with open("doe_degree_of_equivalence.txt", "r", encoding="utf-8") as f:
    doe_data = json.load(f)

with open("pdrv_reference_values.txt", "r", encoding="utf-8") as f:
    ref_value_data = json.load(f)

# Build dictionaries for easier lookup
laboratory_by_name = {entry["Title"]: entry for entry in laboratory_data}
comparison_by_code = {entry["PKacronym_comp_x003a_string"]: entry for entry in code_comparison_data}

# Create XML root with namespaces
NSMAP = {
    None: "PC_RI-II_Schema",
    "kc": "KC_Schema",
    "dsi": "https://ptb.de/si",
    "pc": "PC_RI-II_Schema"
}
root = etree.Element("comparison", nsmap=NSMAP)

# Generating the generalInformation element on comparison and loop over all comparison records
for record in code_comparison_data:
  comparison_code = record.get("PKacronym_comp_x003a_string", "UNKNOWN")

 # <pc:generalInformation>
  general_info = etree.SubElement(root, "{PC_RI-II_Schema}generalInformation")

  # <pc:softwareComparisonCode>
  soft_code = etree.SubElement(general_info, "{PC_RI-II_Schema}softwareComparisonCode")
  soft_code.text = comparison_code
  
  # <pc:serviceCategoryPID>
  service_cat = etree.SubElement(general_info, "{PC_RI-II_Schema}serviceCategoryPID")
  service_cat.text = record.get("service_category_SIDF_x003a_uri", "")
  
  # Determine pilot lab from board_data
  pilot_entry = next(
      (entry for entry in board_data
       if entry.get("field_2") == comparison_code and
          "Pilot" in entry.get("field_5", {}).get("Value", "")),
      None
  )
  
  pilot_acronym = pilot_entry["field_3"] if pilot_entry else "UNKNOWN"
  pilot_lab = laboratory_by_name.get(pilot_acronym, {})
  pilot_ror = pilot_lab.get("ror_identificationA", "UNKNOWN")
  
  # <kc:pilot>
  kc_pilot = etree.SubElement(general_info, "{KC_Schema}pilot")
  
  kc_acr = etree.SubElement(kc_pilot, "{KC_Schema}acronym")
  kc_acr.text = pilot_acronym
  
  kc_ror = etree.SubElement(kc_pilot, "{KC_Schema}ror")
  kc_ror.text = pilot_ror

  # <pc:datasetMeasType>
  dataset_type = etree.SubElement(general_info, "{PC_RI-II_Schema}datasetMeasType")
  dataset_dict = record.get("type_of_data_x003a_liststr", {})
  dataset_type.text = dataset_dict.get("Value", "") if isinstance(dataset_dict, dict) else ""

  # <pc:datasetDownLink>
  dataset_link = etree.SubElement(general_info, "{PC_RI-II_Schema}datasetDownLink")
  dataset_link.text = record.get("link_dataset_x003a_url", "")

  # <kc:linkedComparisonCode>
  kc_linkKCComp = etree.SubElement(general_info, "{KC_Schema}linkedComparisonCode")
  
  kc_compKCCode = etree.SubElement(kc_linkKCComp, "{KC_Schema}comparisonCode")
  kc_compKCCode.text = record.get("acronymum_reference_KC_x003a_str", "")
  
  kc_compKCLink = etree.SubElement(kc_linkKCComp, "{KC_Schema}doi")
  kc_compKCLink.text = record.get("link_reference_KC_x003a_url", "")

  #---------------NEXT SESSION---------------#
  
  # <pc:comparisonData>
comparison_data_elem = etree.SubElement(root, "{PC_RI-II_Schema}comparisonData")

# <kc:comparisonDataType>
comparison_data_type = etree.SubElement(comparison_data_elem, "{KC_Schema}comparisonData")

# 🔁 Loop over KCRVs related to this comparison
for kcrv_entry in [r for r in ref_value_data if r.get("pcrv_comparison") == comparison_code]:

    # <kc:release>
    release_info = etree.SubElement(comparison_data_type, "{KC_Schema}release")

    # <kc:doi>
    kc_doi = etree.SubElement(release_info, "{KC_Schema}doi")
    kc_doi.text = kcrv_entry.get("pcrv_doi_release", "")

    # <kc:year>
    kc_year = etree.SubElement(release_info, "{KC_Schema}year")
    kc_year.text = str(int(kcrv_entry.get("pcrv_year", 0))) if "pcrv_year" in kcrv_entry else ""

    # <kc:kcrv>
    kc_kcrv = etree.SubElement(release_info, "{KC_Schema}kcrv")
    kc_kcrv.text = str(kcrv_entry.get("pcrv_activity_value", ""))

    # 🔁 Add DoEs linked to this KCRV
    for doe in [d for d in doe_data if d.get("doe_reference_pcrv") == kcrv_entry.get("Title")]:
        doe_elem = etree.SubElement(release_info, "{KC_Schema}degreesOfEquivalence")

        lab_elem = etree.SubElement(doe_elem, "lab")
        lab_elem.text = doe.get("doe_laboratory", "")

        val_elem = etree.SubElement(doe_elem, "value")
        val_elem.text = str(doe.get("doe_value", ""))

        unc_elem = etree.SubElement(doe_elem, "stdUnc")
        unc_elem.text = str(doe.get("doe_stdUnc_value", ""))

        unit_elem = etree.SubElement(doe_elem, "unit")
        unit_elem.text = doe.get("doe_unit", {}).get("Value", "")

  #---------------NEXT SESSION---------------#
  
    # <pc:comparisonMetaData>
    comparison_metadata_elem = etree.SubElement(root, "{PC_RI-II_Schema}comparisonMetaData")

    # <kc:comparisonMetaDataType>
    comparison_metadata_type = etree.SubElement(comparison_metadata_elem, "{PC_RI-II_Schema}comparisonDataType")

    # 🔁 Loop over submissions related to this comparison
    for submission_entry in [s for s in comparison_results if s.get("Comparison") == comparison_code]:

        # <pc:submission>
        submission_info = etree.SubElement(comparison_metadata_type, "{PC_RI-II_Schema}submission")

        # Get lab name from current submission entry
        lab_name = submission_entry.get("Laboratory", "UNKNOWN")

        # Find full lab info from lab table
        lab_info = laboratory_by_name.get(lab_name, {})
        lab_acronym = lab_info.get("Title", "UNKNOWN")
        lab_ror = lab_info.get("ror_identificationA", "UNKNOWN")

        # <kc:laboratory>
        kc_lab = etree.SubElement(submission_info, "{KC_Schema}laboratory")
        kc_lab_acronym = etree.SubElement(kc_lab, "{KC_Schema}acronym")
        kc_lab_acronym.text = lab_acronym
        kc_lab_ror = etree.SubElement(kc_lab, "{KC_Schema}ror")
        kc_lab_ror.text = lab_ror

        # <pc:year> from submission's Modified
        pc_year = etree.SubElement(submission_info, "{PC_RI-II_Schema}year")
        modified_date_str = submission_entry.get("Modified", "")
        if modified_date_str:
            modified_date = datetime.fromisoformat(modified_date_str.replace("Z", ""))
            pc_year.text = str(modified_date.year)
        else:
            pc_year.text = ""

        # <pc:inKCRV>: one per comparison
        # Look into ref_value_data for this comparison_code
        has_kcrv = any(
            r.get("pcrv_comparison") == comparison_code and r.get("pcrv_activity_value", 0) != 0
            for r in ref_value_data
        )
        in_kcrv = etree.SubElement(submission_info, "{PC_RI-II_Schema}inKCRV")
        in_kcrv.text = "true" if has_kcrv else "false"

        # <pc:doeValid>: check if there is a DOE for this comparison & lab
        has_doe = any(
            d.get("doe_comparison") == comparison_code and d.get("doe_laboratory") == lab_name and
            d.get("doe_value", 0) not in [0, "", None]
            for d in doe_data
        )
        doe_valid = etree.SubElement(submission_info, "{PC_RI-II_Schema}doeValid")
        doe_valid.text = "true" if has_doe else "false"

        # <pc:laboratoryMeasurements>
        lab_meas_all = etree.SubElement(submission_info, "{PC_RI-II_Schema}laboratoryMeasurements")
        
        # <pc:softwareLabMeasType>
        sub_ref_date = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}referenceDate")
        sub_ref_date.text = submission_entry.get("Created", "UNKNOWN")

        sub_methodID = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}methodID")
        sub_methodID.text = record.get("comparison_metohd_code_x003a_str", "UNKNOWN")

        sub_method_desc = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}description")
        sub_method_desc.text = submission_entry.get("Typeofmeasurement", "UNKNOWN")

        sub_comments = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}comments")
        sub_comments.text = submission_entry.get("comment", "NONE")

        # <pc:activity>
        sub_activity = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}activity")

        # <pc:measurementResult>
        sub_activity_meas = etree.SubElement(sub_activity, "{PC_RI-II_Schema}measurementResult")

        activity_value = etree.SubElement(sub_activity_meas, "{https://ptb.de/si}value")
        activity_value.text = str(submission_entry.get("field_34", ""))

        activity_unit = etree.SubElement(sub_activity_meas, "{https://ptb.de/si}unit")
        activity_unit_dict = submission_entry.get("activity_dsi_unit_x003a_list", {})
        activity_unit.text = activity_unit_dict.get("Value", "") if isinstance(activity_unit_dict, dict) else ""

        # <dsi:measurementUncertaintyUnivariate>
        sub_activity_unc = etree.SubElement(sub_activity_meas, "{https://ptb.de/si}measurementUncertaintyUnivariate")

        # <dsi:measurementUncertaintyUnivariate>
        sub_activity_stdUnc = etree.SubElement(sub_activity_unc, "{https://ptb.de/si}standardMU")

        stdUnc_value = etree.SubElement(sub_activity_stdUnc, "{https://ptb.de/si}valueStandardMU")
        stdUnc_value.text = str(submission_entry.get("field_35", ""))

        sub_effDegOfFree = etree.SubElement(sub_activity, "{PC_RI-II_Schema}effDegreesOfFreedom")
        sub_effDegOfFree.text = str(int(submission_entry.get("effective_degrees_of_freedom_x00", 0)))

        # <pc:activityMetaData>
        sub_activityMD = etree.SubElement(lab_meas_all, "{PC_RI-II_Schema}activityMetaData")

        sub_act_softwareMD = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}activitySoftware")
        sub_act_softwareMD.text = submission_entry.get("ActivityEstimationSoftware", "")

        sub_act_softwareVersionMD = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}activitySoftwareVesion")
        sub_act_softwareVersionMD.text = submission_entry.get("Activity_x0020_Estimation_x0020_", "")

        sub_cnt_softwareMD = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}countingSoftware")
        sub_cnt_softwareMD.text = submission_entry.get("CountingSoftware", "")

        sub_cnt_softwareVersionMD = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}countingSoftwareVersion")
        sub_cnt_softwareVersionMD.text = submission_entry.get("Counting_x0020_Software_x0020_Ve", "")

        sub_typeOfDeadTimeBetaChannel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}typeOfDeadTimeBetaChannel")
        sub_typeOfDeadTimeBetaChannel.text = submission_entry.get("field_6", "")

        sub_typeOfDeadTimeGammaChannel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}typeOfDeadTimeGammaChannel")
        sub_typeOfDeadTimeGammaChannel.text = submission_entry.get("field_7", "")

        sub_coincidenceResolvingTimeBetaChannel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}coincidenceResolvingTimeBetaChannel")
        sub_coincidenceResolvingTimeBetaChannel.text = str(submission_entry.get("field_1", ""))

        sub_coincidenceResolvingTimeGammaChannel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}coincidenceResolvingTimeGammaChannel")
        sub_coincidenceResolvingTimeGammaChannel.text = str(submission_entry.get("field_2", ""))

        sub_deadTimeBetaEvents = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}deadTimeBetaEvents")
        sub_deadTimeBetaEvents.text = str(submission_entry.get("field_4", ""))

        sub_deadTimeGammaEvents = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}deadTimeGammaEvents")
        sub_deadTimeGammaEvents.text = str(submission_entry.get("field_5", ""))

        sub_delayTimeGammaChannel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}delayTimeGammaChannel")
        sub_delayTimeGammaChannel.text = str(submission_entry.get("field_3", ""))

        sub_typeOfAveraging = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}typeOfAveraging")
        sub_typeOfAveraging.text = submission_entry.get("field_29", "")

        sub_typeOfUncertaintyPropagation = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}typeOfUncertaintyPropagation")
        sub_typeOfUncertaintyPropagation.text = submission_entry.get("field_30", "")

        sub_countRateCorrectionType = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}countRateCorrectionType")
        sub_countRateCorrectionType.text = submission_entry.get("field_31", "")

        sub_extrapolationType = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}extrapolationType")
        sub_extrapolationType.text = submission_entry.get("field_32", "")

        sub_correctionAccidentalCoincidences = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}correctionAccidentalCoincidences")
        sub_correctionAccidentalCoincidences.text = submission_entry.get("field_28", "")

        sub_betaSpectrum = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}betaSpectrum")
        sub_betaSpectrum.text = submission_entry.get("tdcr_beta_spectrum_x003a_string", "")

        sub_stoppingPowerModel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}stoppingPowerModel")
        sub_stoppingPowerModel.text = submission_entry.get("tdcr_stopping_power_model_x003a_", "")

        sub_quenchingModel = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}quenchingModel")
        sub_quenchingModel.text = submission_entry.get("tdcr_quenching_model_x003a_strin", "")

        sub_birksConstant = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}birksConstant")
        sub_birksConstant.text = str(submission_entry.get("tdcr_birks_constant_x003a_float", ""))

        sub_lowerIntegrationBound = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}lowerIntegrationBound")
        sub_lowerIntegrationBound.text = str(submission_entry.get("tdcr_lower_integration_bound_x00", ""))

        sub_asymmetryConsidered = etree.SubElement(sub_activityMD, "{PC_RI-II_Schema}asymmetryConsidered")
        sub_asymmetryConsidered.text = str(submission_entry.get("tdcr_asymmetry_considered_x003a_", ""))


tree = etree.ElementTree(root)
tree.write("output_comparison.xml", pretty_print=True, xml_declaration=True, encoding="UTF-8")