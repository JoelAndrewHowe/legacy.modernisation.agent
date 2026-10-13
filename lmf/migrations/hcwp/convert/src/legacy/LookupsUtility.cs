// Extracted bundle file 24; see extract.py and README.md.
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Runtime.Serialization;
using System.Xml.Schema;
using Orvex.Resources;
using Orvex.Contracts.Enums;
using Orvex.TransferObjects;
using HLX.Net2008.Common;

namespace HLX.BusinessTier.Common.Util
{
    public static class LookupsUtility
    {


        /// <summary>
        /// NB. all database values are given as strings at the moment, this may not work for binding int values
        /// </summary>
        public enum DICTIONARY_TYPE
        {
            STRING,
            ENUM
        }
        /*****************************************/



        public enum YES_NO
        {
            [EnumMember]
            YES,
            [EnumMember]
            NO
        }
        public static Dictionary<String, string> YesNo(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Yes", YES_NO.YES.ToString());
                _dict.Add("No", YES_NO.NO.ToString());
            }
            else
            {
                _dict.Add("Yes", "Y");
                _dict.Add("No", "N");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }


        public enum YES_NO_UNKNOWN
        {
            [EnumMember]
            YES,
            [EnumMember]
            NO,
            [EnumMember]
            UNKNOWN
        }
        public static Dictionary<String, string> YesNoUnknown(bool includeNull, DICTIONARY_TYPE dictionaryType, bool useNotKnown = false)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Yes", YES_NO_UNKNOWN.YES.ToString());
                _dict.Add("No", YES_NO_UNKNOWN.NO.ToString());

                _dict.Add(!useNotKnown ? "Unknown" : "Not Known", YES_NO_UNKNOWN.UNKNOWN.ToString());
            }
            else
            {
                _dict.Add("Yes", "Y");
                _dict.Add("No", "N");
                _dict.Add(!useNotKnown ? "Unknown" : "Not Known", "U");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }




        public enum DATE_ESTIMATED
        {
            [EnumMember]
            DAY,
            [EnumMember]
            MONTH,
            [EnumMember]
            NO
        }
        public static Dictionary<String, string> DateEstimated(bool includeNull, DICTIONARY_TYPE dictionaryType, bool includeNo = true)
        {
            Dictionary<String, string> dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                dict.Add("Day", DATE_ESTIMATED.DAY.ToString());
                dict.Add("Month", DATE_ESTIMATED.MONTH.ToString());
                if (includeNo)
                    dict.Add("No", DATE_ESTIMATED.NO.ToString());
            }
            else
            {
                dict.Add("Day", "D");
                dict.Add("Month", "M");
                if (includeNo)
                    dict.Add("No", "N");
            }
            if (includeNull) dict.Add("", null);
            return dict;
        }



        /*****************************************/


        public enum GENDER
        {
            [EnumMember]
            [Display(Name = nameof(Resources.Unknown), ResourceType = typeof(Resources))]
            NOTKNOWN = 0,
            [EnumMember]
            [Display(Name = nameof(Resources.GenderMale), ResourceType = typeof(Resources))]
            MALE = 1,
            [EnumMember]
            [Display(Name = nameof(Resources.GenderFemale), ResourceType = typeof(Resources))]
            FEMALE = 2,
            [EnumMember]
            [Display(Name = nameof(Resources.GenderNotSpecified), ResourceType = typeof(Resources))]
            NOTSPECIFIED = 9
        }
        public static Dictionary<String, string> Gender(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Not Known", GENDER.NOTKNOWN.ToString());
                _dict.Add("Male", GENDER.MALE.ToString());
                _dict.Add("Female", GENDER.FEMALE.ToString());
                _dict.Add("Not Specified", GENDER.NOTSPECIFIED.ToString());
            }
            else
            {
                _dict.Add("Not Known", "0");
                _dict.Add("Male", "1");
                _dict.Add("Female", "2");
                _dict.Add("Not Specified", "9");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }



        public enum LOCATION_TYPE
        {
            [EnumMember]
            [Display(Name = nameof(Resources.TreatmentCentre), ResourceType = typeof(Resources))]
            TREATMENT_CENTRE = 3,

            [EnumMember]
            [Display(Name = nameof(Resources.ExamCentreLabel), ResourceType = typeof(Resources))]
            EXAM_CENTRE = 2,

            [EnumMember]
            [Display(Name = nameof(Resources.School), ResourceType = typeof(Resources))]
            SCHOOL = 1,

            [EnumMember]
            [Display(Name = nameof(Resources.HospitalLabel), ResourceType = typeof(Resources))]
            HOSPITAL = 6,

            [EnumMember]
            [Display(Name = nameof(Resources.WardLabel), ResourceType = typeof(Resources))]
            WARD = 999,

            [EnumMember]
            [Display(Name = nameof(Resources.PracticeLabel), ResourceType = typeof(Resources))]
            PRACTICE = 4

        }

        public static Dictionary<String, string> LocationType(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            var _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Treatment Centre", LOCATION_TYPE.TREATMENT_CENTRE.ToString("D"));
                _dict.Add("Exam Centre", LOCATION_TYPE.EXAM_CENTRE.ToString("D"));
                _dict.Add("School", LOCATION_TYPE.SCHOOL.ToString("D"));
                _dict.Add("Hospital", LOCATION_TYPE.HOSPITAL.ToString("D"));
                _dict.Add("Ward", LOCATION_TYPE.WARD.ToString("D"));
                _dict.Add("Practice", LOCATION_TYPE.PRACTICE.ToString("D"));
            }
            else
            {
                _dict.Add("Treatment Centre", "TC");
                _dict.Add("Exam Centre", "EC");
                _dict.Add("School", "SCH");
                _dict.Add("Hospital", "HOSP");
                _dict.Add("Ward", "WRD");
                _dict.Add("Practice", "PRAC");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }


        public enum EXAM_CONSENT_RESULTS
        {
            [EnumMember]
            NO_CONSENT,
            [EnumMember]
            CONSENT,
            [EnumMember]
            CONSENT_DEFERRED,
            [EnumMember]
            CONSENT_WITHDRAWN,
            [EnumMember]
            CONSENT_REFUSED
        }
        public static Dictionary<EXAM_CONSENT_RESULTS, string> ExamConsentResultMap()
        {
            Dictionary<EXAM_CONSENT_RESULTS, string> _dict = new Dictionary<EXAM_CONSENT_RESULTS, string>();
            _dict.Add(EXAM_CONSENT_RESULTS.CONSENT, "Y");
            _dict.Add(EXAM_CONSENT_RESULTS.NO_CONSENT, "N");
            _dict.Add(EXAM_CONSENT_RESULTS.CONSENT_DEFERRED, "D");
            _dict.Add(EXAM_CONSENT_RESULTS.CONSENT_WITHDRAWN, "W");
            _dict.Add(EXAM_CONSENT_RESULTS.CONSENT_REFUSED, "R");
            return _dict;
        }



        /*****************************************/


        public enum CONSENT_CATEGORY
        {
            [EnumMember]
            IMM = 1,
            [EnumMember]
            PSH = 2,
            [EnumMember]
            NON_ROUTINE_IMM = 3,
            [EnumMember]
            SCHOOL = 4,
            [EnumMember]
            CMP = 5,
            [EnumMember]
            REDUNDANT_CONSENTS = 9
        }
        public static Dictionary<String, string> ConsentCategory(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Immunisation", CONSENT_CATEGORY.IMM.ToString());
                _dict.Add("Pre School", CONSENT_CATEGORY.PSH.ToString());
                _dict.Add("Non-Routine Immunisation", CONSENT_CATEGORY.NON_ROUTINE_IMM.ToString());
                _dict.Add("School", CONSENT_CATEGORY.SCHOOL.ToString());
                _dict.Add("Redundant", CONSENT_CATEGORY.REDUNDANT_CONSENTS.ToString());
            }
            else
            {
                _dict.Add("Immunisation", "1");
                _dict.Add("Pre School", "2");
                _dict.Add("Non-Routine Immunisation", "3");
                _dict.Add("School", "4");
                _dict.Add("Redundant", "9");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }



        public enum ConsentType
        {
            Diphtheria = 1,
            Pertussis = 2,
            Tetanus = 3,
            Polio = 4,
            HIB = 5,
            MenC = 6,
            MMR = 7,
            Pneumococcal = 8,
            BCG = 9,
            HPV = 10,
            PreSchoolMedical = 11,
            PreSchoolVision = 12,
            PreSchoolAudio = 13,
            SwineFlu = 14,
            SchoolAudio = 15,
            SchoolVision = 16,
            SchoolMedical = 17,
            HealthSurveillance = 18,
            Other = 19,
            Height = 20,
            Weight = 21,
            CMP = 23,
            Rotavirus = 24,
            Flu = 25,
            NotRequired = 26,
            MenB = 27,
            MenACWY = 28,
            SocialServices = 29,
            HealthAuthority = 30,
            Education = 31,
            HepatitisB = 32,
        }



        public enum ExaminerType
        {
            [EnumMember]
            EXAM,
            [EnumMember]
            KDP,
            [EnumMember]
            ALL
        }



        public static Dictionary<ExamType, string> ExamTypeCodeMap()
        {
            Dictionary<ExamType, string> _dict = new Dictionary<ExamType, string>();
            _dict.Add(ExamType.MedicalPreschool, "ME");
            _dict.Add(ExamType.AudioPreschool, "AU");
            _dict.Add(ExamType.VisionPreschool, "VI");
            _dict.Add(ExamType.MedicalSchool, "ME");
            _dict.Add(ExamType.AudioSchool, "AU");
            _dict.Add(ExamType.VisionSchool, "VI");
            _dict.Add(ExamType.HealthSurveillance, "HS");
            _dict.Add(ExamType.OtherScreening, "OS");
            _dict.Add(ExamType.Cmp, "CM");
            _dict.Add(ExamType.Kdp, "KD");
            _dict.Add(ExamType.AudioPathway, "AP");
            return _dict;
        }

        public enum IMMUNISATION_STATUS
        {
            [EnumMember]
            [Display(Name = nameof(Resources.TreatmentCentre), ResourceType = typeof(Resources))]
            TREATMENT_CENTRE = 3,
            [EnumMember]
            [Display(Name = nameof(Resources.School), ResourceType = typeof(Resources))]
            SCHOOL = 1,
            [EnumMember]
            [Display(Name = nameof(Resources.OutsideDistrict), ResourceType = typeof(Resources))]
            OUTSIDE_DISTRICT = 0
        }
        public static Dictionary<String, string> ImmunisationStatus(bool includeNull, DICTIONARY_TYPE dictionaryType, bool defaultsOnly = false)
        {
            // Note: defaultsOnly is used for School Authority Options where the default immunisation status can be set.
            // "Outside District" is a valid option for an individual child, but is not valid as a default value.

            var dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                dict.Add("Treatment Centre", IMMUNISATION_STATUS.TREATMENT_CENTRE.ToString());
                dict.Add("School", IMMUNISATION_STATUS.SCHOOL.ToString());
                if (!defaultsOnly)
                    dict.Add("Outside District", IMMUNISATION_STATUS.OUTSIDE_DISTRICT.ToString());
            }
            else
            {
                dict.Add("Treatment Centre", "3");
                dict.Add("School", "1");
                if (!defaultsOnly)
                    dict.Add("Outside District", "0");
            }
            if (includeNull) dict.Add("", null);
            return dict;
        }


        public enum EXAM_STATUS
        {
            [EnumMember]
            EXAM_CENTRE = 1,
            [EnumMember]
            SCHOOL = 3,
            [EnumMember]
            OUTSIDE_DISTRICT = 2
        }
        public static Dictionary<String, string> ExaminationStatus(bool includeNull, DICTIONARY_TYPE dictionaryType, bool defaultsOnly = false)
        {
            // Note: defaultsOnly is used for School Authority Options where the default exam status can be set.
            // "Outside District" is a valid option for an individual child, but is not valid as a default value.

            var dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                dict.Add("Exam Centre", EXAM_STATUS.EXAM_CENTRE.ToString());
                dict.Add("School", EXAM_STATUS.SCHOOL.ToString());
                if (!defaultsOnly)
                    dict.Add("Outside District", EXAM_STATUS.OUTSIDE_DISTRICT.ToString());
            }
            else
            {
                dict.Add("Exam Centre", "1");
                dict.Add("School", "3");
                if (!defaultsOnly)
                    dict.Add("Outside District", "2");
            }
            if (includeNull) dict.Add("", null);
            return dict;
        }


        public enum EXAMINATION_ORIGIN
        {
            [EnumMember]
            SCHEDULED = 1,
            [EnumMember]
            UNSCHEDULED = 2,
            [EnumMember]
            MOVEMENT_IN = 3,
            [EnumMember]
            AMENDMENT = 4,
            [EnumMember]
            NOT_KNOWN = 5,
            [EnumMember]
            OUT_OF_PATHWAY = 6
        }
        public static Dictionary<String, string> ExaminationOrigin(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Scheduled", EXAMINATION_ORIGIN.SCHEDULED.ToString());
                _dict.Add("Unscheduled", EXAMINATION_ORIGIN.UNSCHEDULED.ToString());
                _dict.Add("Movement In", EXAMINATION_ORIGIN.MOVEMENT_IN.ToString());
                _dict.Add("Amendment", EXAMINATION_ORIGIN.AMENDMENT.ToString());
                _dict.Add("Not Known", EXAMINATION_ORIGIN.NOT_KNOWN.ToString());
            }
            else
            {
                _dict.Add("Scheduled", "1");
                _dict.Add("Unscheduled", "2");
                _dict.Add("Movement In", "3");
                _dict.Add("Amendment", "4");
                _dict.Add("Not Known", "5");
            }
            if (includeNull) _dict.Add("", "0");
            return _dict;
        }
        public static Dictionary<string, byte?> ExaminationOrigin()
        {
            return new Dictionary<string, byte?>
            {
                {"Scheduled", 1},
                {"Unscheduled", 2},
                {"Movement In", 3},
                {"Amendment", 4},
                {"Not Known", 5},
            };
        }


        public enum PARENT_PRESENT
        {
            [EnumMember]
            PARENT,
            [EnumMember]
            FOSTER,
            [EnumMember]
            RELATIVE,
            [EnumMember]
            OTHER,
            [EnumMember]
            NOT_PRESENT,
            [EnumMember]
            TELEPHONE
        }
        public static Dictionary<String, string> ParentPresent(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Parent", PARENT_PRESENT.PARENT.ToString());
                _dict.Add("Foster", PARENT_PRESENT.FOSTER.ToString());
                _dict.Add("Relative", PARENT_PRESENT.RELATIVE.ToString());
                _dict.Add("Other", PARENT_PRESENT.OTHER.ToString());
                _dict.Add("Not Present", PARENT_PRESENT.NOT_PRESENT.ToString());
                _dict.Add("Telephone", PARENT_PRESENT.TELEPHONE.ToString());
            }
            else
            {
                _dict.Add("Parent", "P");
                _dict.Add("Foster", "F");
                _dict.Add("Relative", "R");
                _dict.Add("Other", "O");
                _dict.Add("Not Present", "N");
                _dict.Add("Telephone", "T");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }


        public enum VISION_TEST
        {
            [EnumMember]
            SNELLEN = 1,

            [EnumMember]
            SHERIDAN_GARDINER = 2,

            [EnumMember]
            KEYSTONE = 3,

            [EnumMember]
            STYCAR = 4,

            [EnumMember]
            OTHER = 5,

            [EnumMember]
            KAY = 6,

            [EnumMember]
            CATFORD_DRUM = 7,

            [EnumMember]
            LINEAR_SHERIDAN_GARDINER = 8,

            [EnumMember]
            NOT_RECORDED = 9,

            [EnumMember]
            LOGMAR_CROWDED = 10,

            [EnumMember]
            LOGMAR = 11,

            [EnumMember]
            SONKSEN_SILVER = 12
        }
        public static Dictionary<String, string> VisionTest(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("1 - Sellen", VISION_TEST.SNELLEN.ToString());
                _dict.Add("2 - Sheridan Gardner", VISION_TEST.SHERIDAN_GARDINER.ToString());
                _dict.Add("3 - Keystone", VISION_TEST.KEYSTONE.ToString());
                _dict.Add("4 - Stycar", VISION_TEST.STYCAR.ToString());
                _dict.Add("5 - Other", VISION_TEST.OTHER.ToString());
                _dict.Add("6 - Kay", VISION_TEST.KAY.ToString());
                _dict.Add("7 - Catford Drum", VISION_TEST.CATFORD_DRUM.ToString());
                _dict.Add("8 - Linear Sheridan Gardner", VISION_TEST.LINEAR_SHERIDAN_GARDINER.ToString());
                _dict.Add("9 - Not Recorded", VISION_TEST.NOT_RECORDED.ToString());
                _dict.Add("A - LogMAR Crowded", VISION_TEST.LOGMAR_CROWDED.ToString());
                _dict.Add("B - LogMAR", VISION_TEST.LOGMAR.ToString());
                _dict.Add("C - Sonksen Silver", VISION_TEST.SONKSEN_SILVER.ToString());
            }
            else
            {
                _dict.Add("1 - Sellen", "1");
                _dict.Add("2 - Sheridan Gardner", "2");
                _dict.Add("3 - Keystone", "3");
                _dict.Add("4 - Stycar", "4");
                _dict.Add("5 - Other", "5");
                _dict.Add("6 - Kay", "6");
                _dict.Add("7 - Catford Drum", "7");
                _dict.Add("8 - Linear Sheridan Gardner", "8");
                _dict.Add("9 - Not Recorded", "9");
                _dict.Add("A - LogMAR Crowded", "10");
                _dict.Add("B - LogMAR", "11");
                _dict.Add("C - Sonksen Silver", "12");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }



        public enum Dsk
        {
            Locomotor,
            Manipulative,
            Visual,
            Hearing,
            Speech,
            InteractiveSocial,
            SelfCareSocial,
            Cognitive,
        }

        public static Dictionary<string, byte?> EvidenceOfXgm()
        {
            return new Dictionary<string, byte?>
            {
                {"1 - XGM observed", 1},
                {"2 - XGM disclosed", 2},
                {"3 - XGM not present", 3},
                {"4 - Not examined", 4},
                {string.Empty, null}
            };
        }

        public static Dictionary<string, byte?> DomesticViolenceConcern()
        {
            return new Dictionary<string, byte?>
            {
                {"1 - Domestic violence assessment completed", 1},
                {"2 - Domestic violence assessment not completed", 2},
                {string.Empty, null}
            };
        }

        public static Dictionary<string, byte?> DevelopmentAt15And27Months()
        {
            return new Dictionary<string, byte?>
            {
                {"1 - Development as expected", 1},
                {"2 - Concern: requires additional support", 2},
                {string.Empty, null}
            };
        }

        public static Dictionary<string, byte?> PhysicalAssessment6To8Weeks()
        {
            return new Dictionary<string, byte?>
            {
                {"1 - Satisfactory", 1},
                {"2 - Concern", 2},
                {"3 - Not assessed", 3},
                {string.Empty, null}
            };
        }



        public static Dictionary<string, byte?> Outcome()
        {
            return new Dictionary<string, byte?>
            {
                {"Satisfactory", 1},
                {"Unsatisfactory", 2},
                {"Surveillance Only", 3},
                {"Unknown", 4},
                {string.Empty, null}
            };
        }


        /*****************************************/


        public enum Y9Y10_COMPLETED
        {
            [EnumMember]
            Y9,
            [EnumMember]
            Y10,
            [EnumMember]
            BOTH,
            [EnumMember]
            REFUSED,
            [EnumMember]
            NOT_KNOWN
        }
        public static Dictionary<String, string> Y9Y10Completed(bool includeNull, DICTIONARY_TYPE dictionaryType)
        {
            Dictionary<String, string> _dict = new Dictionary<String, string>();
            if (dictionaryType == DICTIONARY_TYPE.ENUM)
            {
                _dict.Add("Y9 Completed", Y9Y10_COMPLETED.Y9.ToString());
                _dict.Add("Y10 Completed", Y9Y10_COMPLETED.Y10.ToString());
                _dict.Add("Both Completed", Y9Y10_COMPLETED.BOTH.ToString());
                _dict.Add("Parent Refused", Y9Y10_COMPLETED.REFUSED.ToString());
                _dict.Add("Not Known", Y9Y10_COMPLETED.NOT_KNOWN.ToString());
            }
            else
            {
                _dict.Add("Y9 Completed", "A");
                _dict.Add("Y10 Completed", "B");
                _dict.Add("Both Completed", "C");
                _dict.Add("Parent Refused", "D");
                _dict.Add("Not Known", "E");
            }
            if (includeNull) _dict.Add("", null);
            return _dict;
        }

        public enum ChildMeasurementType
        {
            [Display(Name = "MeasurementTypeHeight", ResourceType = typeof(Resources))]
            Height,
            [Display(Name = "MeasurementTypeWeight", ResourceType = typeof(Resources))]
            Weight,
            [Display(Name = "MeasurementTypeBMI", ResourceType = typeof(Resources))]
            BMI,
            [Display(Name = "MeasurementTypeHeadCircumference", ResourceType = typeof(Resources))]
            HeadCircumference
        }
        public enum LOCATION_TYPES : byte
        {
            SCHOOL = 1,
            EXAM_CENTRE = 2,
            TREATMENT_CENTRE = 3,
            PRACTICE = 4,
            GP_SURGERY = 5,
            HOSPITAL = 6,
            PCT = 7,
            LHB = 8,
            HSV_TRUST = 9,
            AMBULANCE_TRUST = 10,
            HSV_CARE_TRUST = 11,
            DEPT_OF_HEALTH = 12,
            STRATEGIC_HEALTH_AUTHORITY = 13,
            DEPT_OF_HEALTH_AND_SOCIAL_SERV = 14,
            COMMUNITY_HEALTH_COUNCIL = 15,
            SOFTWARE_SUPPLIER = 16,
            AT_HOME = 17,
            TELEPHONE_CONTACT = 18,
            OUTSIDE_DISTRICT = 19,
            UNKNOWN = 20,
            ALLUSEDACTIVEAUTHORITIES = 99
        }
        public enum PdsFlagCode
        {
            Business,
            Sensitive,
            StopNoted
        }


        public enum CORE_COMPONENT_OFFERED
        {
            [EnumMember]
            UNIVERSAL = 1,

            [EnumMember]
            ENHANCED = 2,

            [EnumMember]
            ENHANCED_PLUS = 3,

            [EnumMember]
            INTENSIVE = 4,

            [EnumMember]
            INTENSIVE_PLUS = 5
        }

        public static Dictionary<string, byte?> CoreComponentOffered()
        {

            Dictionary<string, byte?> _dict = new Dictionary<string, byte?>();
            _dict.Add("1 - Universal", Convert.ToByte(CORE_COMPONENT_OFFERED.UNIVERSAL));
            _dict.Add("2 - Enhanced", Convert.ToByte(CORE_COMPONENT_OFFERED.ENHANCED));
            _dict.Add("3 - Enhanced Plus", Convert.ToByte(CORE_COMPONENT_OFFERED.ENHANCED_PLUS));
            _dict.Add("4 - Intensive", Convert.ToByte(CORE_COMPONENT_OFFERED.INTENSIVE));
            _dict.Add("5 - Intensive Plus", Convert.ToByte(CORE_COMPONENT_OFFERED.INTENSIVE_PLUS));
            return _dict;
        }

        public static Dictionary<string, byte?> CoreComponentOfferedDescription()
        {
            return new Dictionary<string, byte?>
            {
                { "Universal", Convert.ToByte( CORE_COMPONENT_OFFERED.UNIVERSAL)},
                { "Enhanced", Convert.ToByte(CORE_COMPONENT_OFFERED.ENHANCED)},
                { "Enhanced Plus", Convert.ToByte(CORE_COMPONENT_OFFERED.ENHANCED_PLUS)},
                { "Intensive", Convert.ToByte(CORE_COMPONENT_OFFERED.INTENSIVE)},
                { "Intensive Plus", Convert.ToByte(CORE_COMPONENT_OFFERED.INTENSIVE_PLUS)},
                {string.Empty, null}
            };
        }

        public enum WsxNoteTypes
        {
            General = 1,
            Eligibility = 2,
            Consent = 3,
            Administrator_Declaration = 4,
            Adverse_Reaction = 5,
            Suspend = 6,
            Opt_Out = 7
        }
}
}
