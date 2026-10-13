using System; using System.Linq; using Orvex.Model; using Orvex.TransferObjects;
namespace AutoMapper { public static class Mapper {
public static void Map(ChildExamination src, KdpExaminationResultTO dest) {
dest.PkChildExaminationId = src.PkChildExaminationId;
dest.ClientId = src.ClientId;
dest.ExaminationCode = src.FkExaminationId;
dest.OriginalExamCode = src.FkExaminationId;
dest.Sector = src.Sector;
dest.ExamDescription = src.ExaminationDescriptions?.LongDescription;
dest.IsRepeat = src.IsRepeat == "Y";
dest.Origin = src.Origin;
}
public static void Map(ChildExaminationGiven src, KdpExaminationResultTO dest) {
dest.PkChildExaminationId = src.PkFkChildExamGivenId;
dest.LocationType = src.FkLocationHeldTypeId;
dest.LocationCode = src.FkChildLocationHeldCode;
dest.ExaminerType = src.FkStaffTypeExaminerId;
dest.ExaminerHcpCode = src.FkHcpExaminerCode;
dest.ExaminerCategory = src.FkExaminerCatId;
dest.LocationName = src.ChildLocations?.Name;
dest.ReasonNotExamined = src.FkNotExaminedReasonId?.ToString();
dest.ExaminerName = string.Join(" ", src.HealthCareProfessionals?.Name1, src.HealthCareProfessionals?.Name2);
dest.Reschedule = src.RescheduleExamination;
dest.ExaminerTypeDescription = src.Examiner?.Description;
dest.HeightMeasurementDeclined = src.HeightMeasurementRefused;
dest.WeightMeasurementDeclined = src.WeightMeasurementRefused;
dest.HeadMeasurementDeclined = src.HeadMeasurementRefused;
dest.ExaminationDate = src.ExaminationDate;
dest.ResultEnteredDate = src.ResultEnteredDate;
dest.Origin = src.Origin;
}
public static void Map(ChildExaminationKdp src, KdpExaminationResultTO dest) {
dest.PkChildExaminationId = src.PkFkExamKdpGivenId;
dest.ReceivingBoostSchemeService = src.ReceivingBoostScheme;
dest.ReasonNotExaminedDescription = src.ChildExaminationGiven?.ExamNotExaminedReason?.KdpDescription;
dest.Consent = src.Consent;
dest.OnwardReferralsMade = src.OnwardReferralsMade;
dest.LookedAfterChild = src.LookedAfterChild;
dest.OnChildProtectionRegister = src.OnChildProtectionRegister;
dest.EvidenceOfXgm = src.EvidenceOfXgm;
dest.DomesticViolenceConcern = src.DomesticViolenceConcern;
dest.RskResponsiveParenting = src.RskResponsiveParenting;
dest.RskEngagement = src.RskEngagement;
dest.RskSocioFactors = src.RskSocioFactors;
dest.RskFamilyHealth = src.RskFamilyHealth;
dest.RskFamilySupport = src.RskFamilySupport;
dest.RskCompleted = src.RskCompleted;
dest.Development = src.Development;
dest.DevelopmentFurther = src.DevelopmentFurther;
dest.Heart = src.Heart;
dest.Hips = src.Hips;
dest.Eyes = src.Eyes;
dest.Testes = src.Testes;
dest.PhysicalGeneral = src.PhysicalGeneral;
dest.DskLocomotor = src.DskLocomotor;
dest.DskManipulative = src.DskManipulative;
dest.DskVisual = src.DskVisual;
dest.DskHearingAndLanguage = src.DskHearingAndLanguage;
dest.DskSpeechAndLanguage = src.DskSpeechAndLanguage;
dest.DskInteractiveSocial = src.DskInteractiveSocial;
dest.DskSelfCareSocial = src.DskSelfCareSocial;
dest.DskCognitive = src.DskCognitive;
dest.CoreComponent = src.CoreComponent;
}
public static void Map(ChildMeasurement src, KdpExaminationResultTO dest) {
dest.ChildMeasurementId = src.PkChildMeasurementId;
dest.PkChildExaminationId = src.FkChildExaminationId ?? 0;
dest.ClientId = src.ClientId;
dest.Sector = src.Sector;
dest.ExaminationDate = src.MeasurementDate;
dest.Height = src.Height;
dest.Weight = src.Weight;
dest.HeadCircumference = src.HeadCircumference;
}
public static void Map(KdpExaminationResultTO src, ChildExamination dest) {
dest.PkChildExaminationId = src.PkChildExaminationId;
dest.ClientId = src.ClientId;
dest.FkExaminationId = src.ExaminationCode;
dest.Sector = src.Sector;
dest.IsRepeat = src.IsRepeat ? "Y" : "N";
dest.Origin = src.Origin;
}
public static void Map(KdpExaminationResultTO src, ChildExaminationGiven dest) {
dest.PkFkChildExamGivenId = src.PkChildExaminationId;
dest.ExaminationDate = src.ExaminationDate;
dest.FkLocationHeldTypeId = src.LocationType;
dest.FkChildLocationHeldCode = src.LocationCode;
dest.FkStaffTypeExaminerId = src.ExaminerType;
dest.FkHcpExaminerCode = src.ExaminerHcpCode;
dest.FkExaminerCatId = src.ExaminerCategory;
dest.FkNotExaminedReasonId = string.IsNullOrEmpty(src.ReasonNotExamined) ? (byte?)null : Convert.ToByte(src.ReasonNotExamined);
dest.RescheduleExamination = src.Reschedule;
dest.HeightMeasurementRefused = src.HeightMeasurementDeclined;
dest.WeightMeasurementRefused = src.WeightMeasurementDeclined;
dest.HeadMeasurementRefused = src.HeadMeasurementDeclined;
dest.Origin = src.Origin ?? 0;
dest.ResultEnteredDate = src.ResultEnteredDate;
}
public static void Map(KdpExaminationResultTO src, ChildExaminationKdp dest) {
dest.PkFkExamKdpGivenId = src.PkChildExaminationId;
dest.ReceivingBoostScheme = src.ReceivingBoostSchemeService;
dest.Consent = src.Consent;
dest.OnwardReferralsMade = src.OnwardReferralsMade;
dest.LookedAfterChild = src.LookedAfterChild;
dest.OnChildProtectionRegister = src.OnChildProtectionRegister;
dest.EvidenceOfXgm = src.EvidenceOfXgm;
dest.DomesticViolenceConcern = src.DomesticViolenceConcern;
dest.RskResponsiveParenting = src.RskResponsiveParenting;
dest.RskEngagement = src.RskEngagement;
dest.RskSocioFactors = src.RskSocioFactors;
dest.RskFamilyHealth = src.RskFamilyHealth;
dest.RskFamilySupport = src.RskFamilySupport;
dest.RskCompleted = src.RskCompleted;
dest.Development = src.Development;
dest.DevelopmentFurther = src.DevelopmentFurther;
dest.Heart = src.Heart;
dest.Hips = src.Hips;
dest.Eyes = src.Eyes;
dest.Testes = src.Testes;
dest.PhysicalGeneral = src.PhysicalGeneral;
dest.DskLocomotor = src.DskLocomotor;
dest.DskManipulative = src.DskManipulative;
dest.DskVisual = src.DskVisual;
dest.DskHearingAndLanguage = src.DskHearingAndLanguage;
dest.DskSpeechAndLanguage = src.DskSpeechAndLanguage;
dest.DskInteractiveSocial = src.DskInteractiveSocial;
dest.DskSelfCareSocial = src.DskSelfCareSocial;
dest.DskCognitive = src.DskCognitive;
dest.CoreComponent = src.CoreComponent;
}
public static void Map(KdpExaminationResultTO src, ChildMeasurement dest) {
dest.PkChildMeasurementId = src.ChildMeasurementId;
dest.FkChildExaminationId = src.PkChildExaminationId;
dest.ClientId = src.ClientId;
dest.Sector = src.Sector;
dest.MeasurementDate = src.ExaminationDate;
dest.Height = src.Height;
dest.Weight = src.Weight;
dest.HeadCircumference = src.HeadCircumference;
}
public static T Map<T>(object src) where T : new() { var dest=new T(); Map((dynamic)src,(dynamic)dest); return dest; }
}}
