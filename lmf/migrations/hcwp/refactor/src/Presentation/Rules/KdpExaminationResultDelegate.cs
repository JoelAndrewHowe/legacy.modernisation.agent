// Extracted bundle file 6; see extract.py and README.md.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.ServiceModel;
using HLX.BusinessTier.Common.Util;
using HLX.Net2008.Common;
using Orvex.Business.Validation;
using Orvex.Contracts.Enums;
using Orvex.Messages;
using Orvex.Messages.Faults;
using Orvex.Services;
using Orvex.Services.Internal;
using Orvex.TransferObjects;
using OrvexBusinessTierCommon.HLX.BusinessTier.Common.Util;
using static Orvex.Resources.Resources;

namespace Orvex.ViewModels
{
    public class KdpExaminationResultDelegate : ViewModelBase
    {
        private const string NotAssessedCode = "N";
        private const string BmiMeasurmentType = "BMI";
        private const string ExamCode6To8WeekContact = "KD03";
        private readonly string[] examCodeDskContact = { "KD11","KD08","KD09" };
        private readonly string[] examCodes15And27MonthContacts = { "KD08", "KD09" };
        private readonly string[] examCodeRskContact = { "KD01", "KD04", "KD07", "KD08", "KD09", "KD10" };
        private const string DropDownCodeDescriptionFormatExaminer = "{0} - {1}";
        private const string DropDownCodeDescriptionFormatLocation = "{0} - {1}";
        private const string DropDownCodeDescriptionFormatReasonNotExamined = "{0} - {1}";

        private readonly ILookupService lookupsService;
        private readonly KdpExaminationValidator validator;        
        private readonly IChildMeasurementsService measurementsService;
        private readonly Lazy<List<LookupsSubTO>> kdpExaminationList;
        private readonly Lazy<List<ChildMeasurementsRange>> prescribedRanges;
        private readonly Lazy<List<LookupsSubTO>> locationTypesList;
        private readonly Lazy<List<LookupsSubTO>> examinerTypesList;
        private readonly Lazy<List<LookupsSubTO>> notExaminedReasonList;  
      
        private DateTime dateOfBirth;
        private DateTime? dateOfDeath;
        private string gender;
        private List<KdpExaminationResultTO> existingResults;
        private List<LookupsSubTO> locationList;
        private List<LookupsSubTO> examinerList;
        private Lazy<List<ChildMeasurementsRange>> deviationRanges;
        private Lazy<Tuple<double, double>> recommendedAgeRangeInWeeks;
        private Dictionary<LookupsUtility.Dsk, int> dskScoreMaximums;

        protected readonly IMessenger Messenger;
        protected readonly IKdpExaminationService KdpExaminationService;

        public enum TYPE_OF_INPUT { EXAMINER_TYPE, LOCATON_TYPE, REASON_NOT_EXAMINED };
        public List<LookupsSubTO> LocationTypeList => locationTypesList.Value;
        private class TypeCodePosition
        {
            public string TypeCode;
            public string UiPosition;
        }

        List<TypeCodePosition> LocationTypeCodePositions = new List<TypeCodePosition>
        {
            new TypeCodePosition() { TypeCode = "5", UiPosition = "1" },
            new TypeCodePosition() { TypeCode = "2", UiPosition = "2" },
            new TypeCodePosition() { TypeCode = "1", UiPosition = "3" },
            new TypeCodePosition() { TypeCode = "17", UiPosition = "4" },
            new TypeCodePosition() { TypeCode = "6", UiPosition = "5" },
            new TypeCodePosition() { TypeCode = "18", UiPosition = "6" },
            new TypeCodePosition() { TypeCode = "22", UiPosition = "7" }
        };

        List<TypeCodePosition> ExaminerTypeCodePositions = new List<TypeCodePosition>
        {
            new TypeCodePosition() { TypeCode = "17", UiPosition = "1" },
            new TypeCodePosition() { TypeCode = "18", UiPosition = "2" },
            new TypeCodePosition() { TypeCode = "19", UiPosition = "3" },
            new TypeCodePosition() { TypeCode = "20", UiPosition = "4" },
            new TypeCodePosition() { TypeCode = "21", UiPosition = "5" },
            new TypeCodePosition() { TypeCode = "22", UiPosition = "6" },
            new TypeCodePosition() { TypeCode = "23", UiPosition = "7" },
            new TypeCodePosition() { TypeCode = "24", UiPosition = "8" },
            new TypeCodePosition() { TypeCode = "25", UiPosition = "9" },
            new TypeCodePosition() { TypeCode = "26", UiPosition = "10" },
            new TypeCodePosition() { TypeCode = "27", UiPosition = "11" },
            new TypeCodePosition() { TypeCode = "28", UiPosition = "12" }
        };
     
        public List<string> InvalidKdpCodesList { get;set;}
    
        List<TypeCodePosition> ReasonNotExaminedTypeCodePositions = new List<TypeCodePosition>
        {
            new TypeCodePosition() { TypeCode = "1", UiPosition = "1" },
            new TypeCodePosition() { TypeCode = "2", UiPosition = "2" },
            new TypeCodePosition() { TypeCode = "3", UiPosition = "3" },
            new TypeCodePosition() { TypeCode = "4", UiPosition = "4" },
            new TypeCodePosition() { TypeCode = "5", UiPosition = "5" },
        };

        public List<LookupsSubTO> ExaminerTypeList => examinerTypesList.Value;

        public List<LookupsSubTO> NotExaminedReasonList => notExaminedReasonList.Value;

        public Dictionary<string, string> YesNoUnkown => LookupsUtility.YesNoUnknown(false, LookupsUtility.DICTIONARY_TYPE.STRING, true);

        public Dictionary<string, string> YesNoUnkownIncludeNull => LookupsUtility.YesNoUnknown(true, LookupsUtility.DICTIONARY_TYPE.STRING, true);

        public Dictionary<string, string> YesNoIncludeNull => LookupsUtility.YesNo(true, LookupsUtility.DICTIONARY_TYPE.STRING);

        public Dictionary<string, byte?> EvidenceOfXgmList => LookupsUtility.EvidenceOfXgm();

        public Dictionary<string, byte?> DomesticViolenceConcernList => LookupsUtility.DomesticViolenceConcern();

        public Dictionary<string, byte?> DevelopmentAt15And27MonthsList => LookupsUtility.DevelopmentAt15And27Months();

        public Dictionary<string, byte?> PhysicalAssessment6To8WeeksList => LookupsUtility.PhysicalAssessment6To8Weeks();

        public Dictionary<string, byte?> OriginList => LookupsUtility.ExaminationOrigin();

        public Dictionary<string, byte?> CoreComponentOfferedList => LookupsUtility.CoreComponentOffered();

        public List<LookupsSubTO> KdpExaminationList => kdpExaminationList.Value;
        public bool ExamCodeValidated { private get; set; }
        public bool IsScheduled { get; set; }
        public bool IsUnscheduled => !IsScheduled;
        public KdpExaminationResultTO KdpExaminationResultTo { get; set; }

        public KdpExaminationResultDelegate(KdpExaminationValidator validator, IMessenger messenger, ILookupService lookupsService, IChildMeasurementsService measurementsService, IKdpExaminationService service)
        {
            this.validator = validator;
            this.lookupsService = lookupsService;
            Messenger = messenger;
            this.measurementsService = measurementsService;
            KdpExaminationService = service;

            kdpExaminationList = new Lazy<List<LookupsSubTO>>(() => lookupsService.getLookups(TypeOfLookup.AllExams, string.Empty, ExamType.Kdp.ToString()));
            prescribedRanges = new Lazy<List<ChildMeasurementsRange>>(measurementsService.GetPrescribedRanges);
            locationTypesList = new Lazy<List<LookupsSubTO>>(() => lookupsService.getLookups(TypeOfLookup.ExamLocationTypeKdp, string.Empty, string.Empty));
            examinerTypesList = new Lazy<List<LookupsSubTO>>(() => lookupsService.getLookups(TypeOfLookup.ExaminerByPrimaryKeyKdp, string.Empty, string.Empty));
            notExaminedReasonList = new Lazy<List<LookupsSubTO>>(() => lookupsService.getLookups(TypeOfLookup.ExamNotExaminedReasonKdp, string.Empty, string.Empty), true);

            PropertyChanged += CheckBmi;
            InvalidKdpCodesList = ExaminerTypeCodePositions.Where(x => !("18,19,26,28".Split(',')).Contains( x.TypeCode.ToString())).Select(invalid=> invalid.TypeCode.ToString() ).ToList();
        }

        public void Populate(KdpExaminationResultTO kdpExaminationResultTo, string gender, DateTime dateOfBirth, DateTime? dateOfDeath, List<KdpExaminationResultTO> existingResults, bool isScheduled = false)
        {
            KdpExaminationResultTo = kdpExaminationResultTo;
            this.gender = gender;
            this.dateOfDeath = dateOfDeath;
            this.dateOfBirth = dateOfBirth;
            this.existingResults = existingResults;
            ResetDeviations();
            ResetRecommendedAgeRange();
            IsScheduled = isScheduled;
            UpdateExamDescription();
            PrependNumericsUiExaminerDescriptions();
            PrependNumericsUiLocationTypeDescriptions();
            PrependNumericsUiReasonNotExaminedDescriptions();
        }

        public Dictionary<string, string> DskScores(LookupsUtility.Dsk dskSkill)
        {
            dskScoreMaximums = dskScoreMaximums ?? new Dictionary<LookupsUtility.Dsk, int>
            {
                {LookupsUtility.Dsk.Locomotor, 20},
                {LookupsUtility.Dsk.Manipulative, 28},
                {LookupsUtility.Dsk.Visual, 20},
                {LookupsUtility.Dsk.Hearing, 21},
                {LookupsUtility.Dsk.Speech, 22},
                {LookupsUtility.Dsk.InteractiveSocial, 24},
                {LookupsUtility.Dsk.SelfCareSocial, 23},
                {LookupsUtility.Dsk.Cognitive, 34}
            };
            var dict = Enumerable.Range(0, dskScoreMaximums[dskSkill] + 1).Select(n => n.ToString()).ToDictionary(i => i);
            dict.Add(KdpResultsNotAssessedDescription, NotAssessedCode);
            return dict;
        }

        public Dictionary<string, byte?> RskScores => Enumerable.Range(1, 5).Select(n => (byte?)n).ToDictionary(s => s.ToString());

        public long PkChildExaminationId
        {
            get { return KdpExaminationResultTo.PkChildExaminationId; }
            set { KdpExaminationResultTo.PkChildExaminationId = value; }
        }
        public string ExaminationCode
        {
            get { return KdpExaminationResultTo.ExaminationCode; }
            set
            {
                if (!ExamCodeValidated || KdpExaminationResultTo.ExaminationCode == value)
                    return;

                KdpExaminationResultTo.ExaminationCode = value;
                UpdateExamDescription();
                RaisePropertyChanged(nameof(Is15Or27MonthContact));
                RaisePropertyChanged(nameof(Is6To8WeekContact));
                RaisePropertyChanged(nameof(IsDskContact));
                RaisePropertyChanged(nameof(IsRskContact));
                ClearDataFromHiddenFields();
                ResetRecommendedAgeRange();
            }
        }

        private void UpdateExamDescription()
        {
            KdpExaminationResultTo.ExamDescription = KdpExaminationList
                .SingleOrDefault(ex => ex.Code == KdpExaminationResultTo.ExaminationCode)
                    ?.Description;

            if (KdpExaminationResultTo.IsRepeat && KdpExaminationResultTo.ExaminationCode == KdpExaminationResultTo.OriginalExamCode
                && KdpExaminationResultTo.Lock == null)
                KdpExaminationResultTo.ExamDescription += RecallText;

            RaisePropertyChanged(nameof(ExamDescription));
        }

        public string ResultTabText => ExaminationCode + (KdpExaminationResultTo.IsRepeat ? RecallFlag : string.Empty);

        public bool Is15Or27MonthContact => examCodes15And27MonthContacts.Contains(KdpExaminationResultTo.ExaminationCode);
        public bool IsRskContact => examCodeRskContact.Contains(KdpExaminationResultTo.ExaminationCode);
        public bool Is6To8WeekContact => KdpExaminationResultTo.ExaminationCode == ExamCode6To8WeekContact;
        public bool IsDskContact => examCodeDskContact.Contains(KdpExaminationResultTo.ExaminationCode);
        public DateTime ExaminationDate
        {
            get { return KdpExaminationResultTo.ExaminationDate; }
            set {
                if (KdpExaminationResultTo.ExaminationDate.Date != value.Date)
                {
                    KdpExaminationResultTo.ExaminationDate = new DateTime(value.Year, value.Month, value.Day, KdpExaminationResultTo.ExaminationDate.Hour, KdpExaminationResultTo.ExaminationDate.Minute, KdpExaminationResultTo.ExaminationDate.Second);
                    ResetDeviations();
                }
            }
        }
        public string ReasonNotExamined
        {
            get { return KdpExaminationResultTo.ReasonNotExamined; }
            set { KdpExaminationResultTo.ReasonNotExamined = value; }
        }
        public string Consent
        {
            get { return KdpExaminationResultTo.Consent; }
            set { KdpExaminationResultTo.Consent = value; }
        }
        public byte? LocationType
        {
            get { return KdpExaminationResultTo.LocationType; }
            set
            {
                KdpExaminationResultTo.LocationType = value;
                KdpExaminationResultTo.LocationCode = string.Empty;
                KdpExaminationResultTo.LocationName = string.Empty;
                locationList = null;
            }
        }
        public string LocationCode
        {
            get { return KdpExaminationResultTo.LocationCode; }
            set
            {
                KdpExaminationResultTo.LocationCode = value;
                KdpExaminationResultTo.LocationName = string.IsNullOrEmpty(KdpExaminationResultTo.LocationCode)
                    ? string.Empty
                    : locationList?.SingleOrDefault(lc => lc.Code == KdpExaminationResultTo.LocationCode)?.Description;
            }
        }
        public string ExaminerKdpCode
        {
            get { return KdpExaminationResultTo.ExaminerHcpCode; }
            set
            {
                KdpExaminationResultTo.ExaminerHcpCode = value;
                PopulateHcpDetails();
            }
        }

        private void PopulateHcpDetails()
        {
            if (string.IsNullOrEmpty(KdpExaminationResultTo.ExaminerHcpCode))
            {
                ExaminerName = string.Empty;
                ExaminerCategory = string.Empty;
            }
            else
            {
                var hcp = examinerList.FirstOrDefault(ex => ex.UsedCode == HLXBoolean.True && ex.Code == ExaminerKdpCode);
                ExaminerName = hcp?.Description;
                ExaminerType = hcp?.Type;
            }
        }
        public string ExaminerType
        {
            get { return KdpExaminationResultTo.ExaminerType; }
            set
            {
                KdpExaminationResultTo.ExaminerType = value;
            }
        }
        public string ExaminerCategory
        {
            get { return KdpExaminationResultTo.ExaminerCategory; }
            set
            {
                KdpExaminationResultTo.ExaminerCategory = value;
                KdpExaminationResultTo.ExaminerType = string.Empty;
                KdpExaminationResultTo.ExaminerHcpCode = string.Empty;
                KdpExaminationResultTo.ExaminerName = string.Empty;
                examinerList = null;
            }
        }
        public decimal BmiLowerBound => (decimal)prescribedRanges.Value.SingleOrDefault(d => d.MeasurementType == BmiMeasurmentType).LowerBound;
        public decimal BmiUpperBound => (decimal)prescribedRanges.Value.SingleOrDefault(d => d.MeasurementType == BmiMeasurmentType).UpperBound;
        public decimal? Bmi => (Height.HasValue && Weight.HasValue) ? measurementsService.CalculateBmi(Height.Value, Weight.Value) : null;
        public bool IsBmiOutsideRange => Bmi.HasValue && (Bmi < BmiLowerBound || BmiUpperBound < Bmi);
        public bool IsHeightRequired => !IsHeightDeclined;
        public bool IsWeightRequired => !IsWeightDeclined;
        public bool IsHeadCircumferenceRequired => !IsHeadCircumferenceDeclined;
        public bool IsHeightDeclined
        {
            get
            {
                return KdpExaminationResultTo.HeightMeasurementDeclined == HLXBoolean.True;
            }
            set
            {
                KdpExaminationResultTo.HeightMeasurementDeclined = value ? HLXBoolean.True : HLXBoolean.False;
                RaisePropertyChanged(nameof(IsHeightRequired));
                Height = null;
            }
        }

        public bool IsWeightDeclined
        {
            get
            {
                return KdpExaminationResultTo.WeightMeasurementDeclined == HLXBoolean.True;
            }
            set
            {
                KdpExaminationResultTo.WeightMeasurementDeclined = value ? HLXBoolean.True : HLXBoolean.False;
                RaisePropertyChanged(nameof(IsWeightRequired));
                Weight = null;
            }
        }

        public bool IsHeadCircumferenceDeclined
        {
            get
            {
                return KdpExaminationResultTo.HeadMeasurementDeclined == HLXBoolean.True;
            }
            set
            {
                KdpExaminationResultTo.HeadMeasurementDeclined = value ? HLXBoolean.True : HLXBoolean.False;
                RaisePropertyChanged(nameof(IsHeadCircumferenceRequired));
                HeadCircumference = null;
            }
        }

        public decimal? Height
        {
            get
            {
                return KdpExaminationResultTo.Height;
            }
            set
            {
                KdpExaminationResultTo.Height = value;
                RaisePropertyChanged(nameof(Bmi));
                RaisePropertyChanged(nameof(IsBmiOutsideRange));
            }
        }
        public decimal? Weight
        {
            get
            {
                return KdpExaminationResultTo.Weight;
            }
            set
            {
                KdpExaminationResultTo.Weight = value;
                RaisePropertyChanged(nameof(Bmi));
                RaisePropertyChanged(nameof(IsBmiOutsideRange));
            }
        }
        public decimal? HeadCircumference
        {
            get { return KdpExaminationResultTo.HeadCircumference; }
            set
            {
                KdpExaminationResultTo.HeadCircumference = value;
                RaisePropertyChanged(nameof(HeadCircumference));
            }
        }

        public string OnwardReferralsMade
        {
            get { return KdpExaminationResultTo.OnwardReferralsMade; }
            set { KdpExaminationResultTo.OnwardReferralsMade = value; }
        }
        public string ReceivingBoostSchemeService
        {
            get { return KdpExaminationResultTo.ReceivingBoostSchemeService; }
            set { KdpExaminationResultTo.ReceivingBoostSchemeService = value; }
        }
        public string LookedAfterChild
        {
            get { return KdpExaminationResultTo.LookedAfterChild; }
            set { KdpExaminationResultTo.LookedAfterChild = value; }
        }
        public string OnChildProtectionRegister
        {
            get { return KdpExaminationResultTo.OnChildProtectionRegister; }
            set { KdpExaminationResultTo.OnChildProtectionRegister = value; }
        }
        public byte? EvidenceOfXgm
        {
            get { return KdpExaminationResultTo.EvidenceOfXgm; }
            set { KdpExaminationResultTo.EvidenceOfXgm = value; }
        }
        public byte? DomesticViolenceConcern
        {
            get { return KdpExaminationResultTo.DomesticViolenceConcern; }
            set { KdpExaminationResultTo.DomesticViolenceConcern = value; }
        }
        public byte? RskResponsiveParenting
        {
            get { return KdpExaminationResultTo.RskResponsiveParenting; }
            set { KdpExaminationResultTo.RskResponsiveParenting = value; }
        }
        public byte? RskEngagement
        {
            get { return KdpExaminationResultTo.RskEngagement; }
            set { KdpExaminationResultTo.RskEngagement = value; }
        }
        public byte? RskSocioFactors
        {
            get { return KdpExaminationResultTo.RskSocioFactors; }
            set { KdpExaminationResultTo.RskSocioFactors = value; }
        }
        public byte? RskFamilyHealth
        {
            get { return KdpExaminationResultTo.RskFamilyHealth; }
            set { KdpExaminationResultTo.RskFamilyHealth = value; }
        }
        public byte? RskFamilySupport
        {
            get { return KdpExaminationResultTo.RskFamilySupport; }
            set { KdpExaminationResultTo.RskFamilySupport = value; }
        }

        public byte? CoreComponentOffered
        {
            get { return KdpExaminationResultTo.CoreComponent; }
            set { KdpExaminationResultTo.CoreComponent = value; }
        }

        public string RskCompleted
        {
            get { return KdpExaminationResultTo.RskCompleted; }
            set { KdpExaminationResultTo.RskCompleted = value; }
        }
        public byte? Development
        {
            get { return KdpExaminationResultTo.Development; }
            set { KdpExaminationResultTo.Development = value; }
        }
        public string DevelopmentFurther
        {
            get { return KdpExaminationResultTo.DevelopmentFurther; }
            set { KdpExaminationResultTo.DevelopmentFurther = value; }
        }
        public byte? Heart
        {
            get { return KdpExaminationResultTo.Heart; }
            set { KdpExaminationResultTo.Heart = value; }
        }
        public byte? Hips
        {
            get { return KdpExaminationResultTo.Hips; }
            set { KdpExaminationResultTo.Hips = value; }
        }
        public byte? Eyes
        {
            get { return KdpExaminationResultTo.Eyes; }
            set { KdpExaminationResultTo.Eyes = value; }
        }
        public byte? Testes
        {
            get { return KdpExaminationResultTo.Testes; }
            set { KdpExaminationResultTo.Testes = value; }
        }
        public byte? PhysicalGeneral
        {
            get { return KdpExaminationResultTo.PhysicalGeneral; }
            set { KdpExaminationResultTo.PhysicalGeneral = value; }
        }
        public string Reschedule
        {
            get { return KdpExaminationResultTo.Reschedule; }
            set { KdpExaminationResultTo.Reschedule = value; }
        }

        public bool WithdrawConsent
        {
            get { return KdpExaminationResultTo.WithdrawConsent; }
            set { KdpExaminationResultTo.WithdrawConsent = value; }
        }

        public string DskLocomotor
        {
            get { return KdpExaminationResultTo.DskLocomotor; }
            set { KdpExaminationResultTo.DskLocomotor = value; }
        }
        public string DskManipulative
        {
            get { return KdpExaminationResultTo.DskManipulative; }
            set { KdpExaminationResultTo.DskManipulative = value; }
        }
        public string DskVisual
        {
            get { return KdpExaminationResultTo.DskVisual; }
            set { KdpExaminationResultTo.DskVisual = value; }
        }
        public string DskHearingAndLanguage
        {
            get { return KdpExaminationResultTo.DskHearingAndLanguage; }
            set { KdpExaminationResultTo.DskHearingAndLanguage = value; }
        }
        public string DskSpeechAndLanguage
        {
            get { return KdpExaminationResultTo.DskSpeechAndLanguage; }
            set { KdpExaminationResultTo.DskSpeechAndLanguage = value; }
        }
        public string DskInteractiveSocial
        {
            get { return KdpExaminationResultTo.DskInteractiveSocial; }
            set { KdpExaminationResultTo.DskInteractiveSocial = value; }
        }
        public string DskSelfCareSocial
        {
            get { return KdpExaminationResultTo.DskSelfCareSocial; }
            set { KdpExaminationResultTo.DskSelfCareSocial = value; }
        }
        public string DskCognitive
        {
            get { return KdpExaminationResultTo.DskCognitive; }
            set { KdpExaminationResultTo.DskCognitive = value; }
        }
        public string ExamDescription
        {
            get
            {
                if (KdpExaminationResultTo.IsRepeat && KdpExaminationResultTo.ExaminationCode == KdpExaminationResultTo.OriginalExamCode)
                    return KdpExaminationResultTo.ExamDescription + RecallText;

                return KdpExaminationResultTo.ExamDescription;
            }
            set { KdpExaminationResultTo.ExamDescription = value; }
        }
        public string ExaminerName
        {
            get { return KdpExaminationResultTo.ExaminerName; }
            set { KdpExaminationResultTo.ExaminerName = value; }
        }
        public string LocationName
        {
            get { return KdpExaminationResultTo.LocationName; }
            set { KdpExaminationResultTo.LocationName = value; }
        }

        public byte? Origin
        {
            get { return KdpExaminationResultTo.Origin; }
            set { KdpExaminationResultTo.Origin = value; }
        }

        public bool ValidateAndSetExamCode(string examCode)
        {
            ExamCodeValidated = false;

            try
            {
                validator.ValidateExamCodeForDate(existingResults, PkChildExaminationId, examCode, ExaminationDate);
                validator.ValidateNewExamCode(examCode, KdpExaminationList);

                if (KdpExaminationResultTo.ExaminationCode != examCode)
                {
                    validator.ValidateExamCodeForDuplicates(existingResults, examCode, PkChildExaminationId);
                }
            }
            catch (FaultException<ValidationWarningFault> ex)
            {
                var confirmation = new YesNoConfirmationRequiredMessage(ex.Message, KdpResultsTitle, ex.Detail.Title);
                Messenger.Send(confirmation);
                if (!confirmation.Response)
                {
                    return false;
                }
            }
            catch (FaultException<ValidationFault> ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ex.Detail.Title);
                Messenger.Send(error);
                return false;
            }

            if (!string.IsNullOrEmpty(KdpExaminationResultTo.ExaminationCode) && KdpExaminationResultTo.ExaminationCode != examCode)
            {
                var confirmation = new YesNoConfirmationRequiredMessage(KdpResultsExamCodeChangeConfirmationMessage, KdpResultsTitle, KdpResultsExamCodeChangeConfirmationPrompt);
                Messenger.Send(confirmation);
                if (!confirmation.Response)
                {
                    return false;
                }
            }

            ExamCodeValidated = true;
            ExaminationCode = examCode;
            return true;
        }

        public bool ValidateExaminationDate(DateTime examDate)
        {
            try
            {
                validator.ValidateExaminationDate(examDate, dateOfBirth, dateOfDeath);
                validator.ValidateExamCodeForDate(existingResults, PkChildExaminationId, ExaminationCode, examDate);
            }
            catch (FaultException<ValidationFault> ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ex.Detail.Title);
                Messenger.Send(error);
                return false;
            }

            CheckAgeWithinScheduleRange(examDate);

            return true;
        }

        public bool ValidateHeight(decimal? height)
        {
            try
            {
                validator.ValidateHeight(height);
                CheckDeviations(height, LookupsUtility.ChildMeasurementType.Height);
                return true;
            }
            catch (FaultException<ValidationFault> ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ex.Detail.Title);
                Messenger.Send(error);
                return false;
            }
        }

        public bool ValidateWeight(decimal? weight)
        {
            try
            {
                validator.ValidateWeight(weight);
                CheckDeviations(weight, LookupsUtility.ChildMeasurementType.Weight);
                return true;
            }
            catch (FaultException<ValidationFault> ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ex.Detail.Title);
                Messenger.Send(error);
                return false;
            }
        }

        public bool ValidateHeadCircumference(decimal headCircumference)
        {   
            try
            {
                validator.ValidateHeadCircumference(headCircumference);
                 return true;
             }
             catch (FaultException<ValidationFault> ex)
             {
                var error = new NonFatalErrorEncountered(ex.Message, KdpResultsTitle,ex.Detail.Title);
                 Messenger.Send(error);
                 return false;
             }
        }

        public bool ValidateLocationCode(string code)
        {
            if (string.IsNullOrEmpty(code))
            {
                return true;
            }

            GetLocationList();

            if (locationList != null && locationList.All(loc => loc.Code != code))
            {
                Messenger.Send(new NonFatalErrorEncountered(string.Format(InvalidLocationCodeMessage, code), KdpResultsTitle, InvalidLocationCodePrompt));
                return false;
            }

            return true;
        }

        public bool ValidateExaminerCode(string code)
        {
            if (string.IsNullOrEmpty(code))
            {
                return true;
            }

            GetExaminerList();

            if (examinerList == null)
                return true;

            var selectedExaminer = examinerList.FirstOrDefault(ex => ex.Code == code);

            if (selectedExaminer == null)
            {
                Messenger.Send(new NonFatalErrorEncountered(string.Format(InvalidHcpCodeMessage, code), KdpResultsTitle, InvalidHcpCodePrompt));
                return false;
            }

            if (selectedExaminer.UsedCode == HLXBoolean.False)
            {
                Messenger.Send(new NonFatalErrorEncountered(UnusedExaminerCodeMessage, KdpResultsTitle, UnusedExaminerCodePrompt));
                return false;
            }

            return true;
        }
        private void CheckDeviations(decimal? measurementValue, LookupsUtility.ChildMeasurementType measurementType)
        {

            if (ExaminationDate <= DateTime.MinValue || measurementValue == null)
                return;

            var deviationRange = deviationRanges.Value.SingleOrDefault(d => d.MeasurementType == measurementType.ToString());
            var value = (double)measurementValue;

            if (deviationRange.LowerBound < deviationRange.UpperBound && deviationRange.LowerBound < value && value < deviationRange.UpperBound )
                return;

            var warningMessage = string.Format(OutsideExpectedRangeMessage, measurementType.GetDisplayName());
            Messenger.Send(new WarningNotificationMessage(warningMessage, KdpResultsTitle, OutsideExpectedRangePrompt));
        }

        private void CheckBmi(object sender, PropertyChangedEventArgs eventArgs)
        {
            if (eventArgs.PropertyName == nameof(Bmi) && IsBmiOutsideRange)
            {
                Messenger.Send(
                    new WarningNotificationMessage(
                        string.Format(BmiOutsidePrescribedRangeMessage, BmiLowerBound, BmiUpperBound), 
                        KdpResultsTitle,
                        OutsidePrescribedRangePrompt));
            }
        }

        private void CheckAgeWithinScheduleRange(DateTime examDate)
        {
            if (string.IsNullOrEmpty(ExaminationCode)) return;

            var ageInWeeks = dateOfBirth.WeeksBetween(examDate);
            var ageRange = recommendedAgeRangeInWeeks.Value;

            if (ageRange != null && ageRange.Item2 > 0)
            {
                if (ageInWeeks < ageRange.Item1 || ageRange.Item2 < ageInWeeks)
                {
                    {
                        var warningMessage = ageInWeeks < ageRange.Item1? KdpContactGivenBeforeMinAge: KdpContactGivenAfterMaxAge;
                        var warning = new WarningNotificationMessage(string.Format(warningMessage, ExaminationCode),KdpResultsTitle, WarningPrompt);

                        Messenger.Send(warning);
                    }
                }
            }
        }

        public bool ValidateNumericDescriptorEntered(string input, TYPE_OF_INPUT type)
        {
            int output;
            if (int.TryParse(input, out output))
            {
                List<TypeCodePosition> comparitiveList = type == TYPE_OF_INPUT.EXAMINER_TYPE ? ExaminerTypeCodePositions
                                        : type == TYPE_OF_INPUT.LOCATON_TYPE ? LocationTypeCodePositions
                                        : type == TYPE_OF_INPUT.REASON_NOT_EXAMINED ? ReasonNotExaminedTypeCodePositions
                                        : null;
                
                if(comparitiveList != null && !comparitiveList.Any(c => Convert.ToInt16(c.UiPosition) == output))
                {
                    return false;
                }

                return true;
            }

            return true;
        }

        public List<LookupsSubTO> GetLocationList()
        {
            if (KdpExaminationResultTo.LocationType == null)
            {
                Messenger.Send(new NonFatalErrorEncountered(NoLocationTypeMessage, KdpResultsTitle, NoLocationTypePrompt));
                return null;
            }

            try
            {
                 locationList = locationList ?? lookupsService.getLookups(TypeOfLookup.Locations, string.Empty, KdpExaminationResultTo.LocationType.ToString());
                return locationList;
            }
            catch (FaultException ex)
            {
                Messenger.Send(new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ErrorGettingLocationListPrompt));
                return null;
            }
        }

        public List<LookupsSubTO> GetUsedExaminerList()
        {
            return GetExaminerList()?.Where(ex => ex.UsedCode == HLXBoolean.True).ToList();
        }

        private List<LookupsSubTO> GetExaminerList()
        {
            if (string.IsNullOrEmpty(KdpExaminationResultTo.ExaminerCategory))
            {
                Messenger.Send(new NonFatalErrorEncountered(NoExaminerTypeMessage, KdpResultsTitle, NoExaminerTypePrompt));
                return null;
            }

            try
            {
                examinerList = examinerList ?? lookupsService.getLookupsByUsed(TypeOfLookup.Examiners, string.Empty, KdpExaminationResultTo.ExaminerCategory, HLXBoolean.False);
                return examinerList;
            }
            catch (FaultException ex)
            {
                Messenger.Send(new NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ErrorGettingExaminerListPrompt));
                return null;
            }
        }

        public int ChangesCount => KdpExaminationResultTo.PropertyChanged.Count;

        private void ClearDataFromHiddenFields()
        {
            if (!Is15Or27MonthContact)
            {
                Development = null;
                DevelopmentFurther = null;
            }

            if (!Is6To8WeekContact)
            {
                Heart = null;
                Hips = null;
                Eyes = null;
                Testes = null;
                PhysicalGeneral = null;
            }

            if (!IsDskContact)
            {
                DskLocomotor = null;
                DskManipulative = null;
                DskVisual = null;
                KdpExaminationResultTo.DskHearingAndLanguage = null;
                KdpExaminationResultTo.DskSpeechAndLanguage = null;
                DskInteractiveSocial = null;
                DskSelfCareSocial = null;
                DskCognitive = null;
            }

            if (IsRskContact) return;
            KdpExaminationResultTo.RskResponsiveParenting = null;
            KdpExaminationResultTo.RskEngagement = null;
            KdpExaminationResultTo.RskSocioFactors = null;
            RskFamilyHealth = null;
            RskFamilySupport = null;
            RskCompleted = null;
        }

        private void ResetDeviations()
        {
            deviationRanges = new Lazy<List<ChildMeasurementsRange>>(() => measurementsService.GetExpectedRanges(gender, dateOfBirth, ExaminationDate));
        }

        private void ResetRecommendedAgeRange()
        {
            recommendedAgeRangeInWeeks = new Lazy<Tuple<double, double>>(() => KdpExaminationService.GetAgeRangeFromExamSchedule(ExaminationCode));
        }

        public void LookUpExamCode()
        {
            var examLookup = new ShowFormLookup(KdpExaminationList);
            Messenger.Send(examLookup);

            if (string.IsNullOrEmpty(examLookup.Values))
                return;

            ValidateAndSetExamCode(examLookup.Values);
        }

        private string GetDropDownUiPositionNumber(string typeCode, List<TypeCodePosition> typeCodePositions)
        {
            string uiPostionNumber = typeCodePositions.Where(x => x.TypeCode == typeCode).Select(x => x.UiPosition).FirstOrDefault();

            return uiPostionNumber;
        }

        private void PrependNumericsUiLocationTypeDescriptions()
        {
            foreach (var location in LocationTypeList)
            {
                string uiLocationPositionNumber = GetDropDownUiPositionNumber(location.Code, LocationTypeCodePositions);

                if (!string.IsNullOrEmpty(uiLocationPositionNumber))
                {
                    if (!location.Description.StartsWith(uiLocationPositionNumber))
                        location.Description = string.Format(DropDownCodeDescriptionFormatLocation, uiLocationPositionNumber, location.Description);
                }
            }
        }

        private void PrependNumericsUiExaminerDescriptions()
        {
            foreach (var examiner in ExaminerTypeList)
            {
                string uiExaminerPositionNumber = GetDropDownUiPositionNumber(examiner.Code, ExaminerTypeCodePositions);

                if (!string.IsNullOrEmpty(uiExaminerPositionNumber))
                {
                    if (!examiner.Description.StartsWith(uiExaminerPositionNumber))
                        examiner.Description = string.Format(DropDownCodeDescriptionFormatExaminer, uiExaminerPositionNumber, examiner.Description);
                }
            }
        }

        private void PrependNumericsUiReasonNotExaminedDescriptions()
        {
            foreach (var reasonNotExamined in NotExaminedReasonList)
            {
                string uiReasonNotExaminedPositionNumber = GetDropDownUiPositionNumber(reasonNotExamined.Code, ReasonNotExaminedTypeCodePositions);

                if (!string.IsNullOrEmpty(uiReasonNotExaminedPositionNumber))
                {
                    if (!reasonNotExamined.Description.StartsWith(uiReasonNotExaminedPositionNumber))
                        reasonNotExamined.Description = string.Format(DropDownCodeDescriptionFormatReasonNotExamined, uiReasonNotExaminedPositionNumber, reasonNotExamined.Description);
                }
            }
        }

    }
}
