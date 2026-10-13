// Extracted bundle file 72; see extract.py and README.md.
using System.ComponentModel.DataAnnotations;

namespace Orvex.Model
{
    public class ChildExaminationKdp
    {
        public long PkFkExamKdpGivenId { get; set; }
        public string Consent { get; set; }
        public string OnwardReferralsMade { get; set; }
        public string ReceivingBoostScheme { get; set; }
        public string LookedAfterChild { get; set; }
        public string OnChildProtectionRegister { get; set; }
        public byte? EvidenceOfXgm { get; set; }
        public byte? DomesticViolenceConcern { get; set; }
        public byte? RskResponsiveParenting { get; set; }
        public byte? RskEngagement { get; set; }
        public byte? RskSocioFactors { get; set; }
        public byte? RskFamilyHealth { get; set; }
        public byte? RskFamilySupport { get; set; }
        public string RskCompleted { get; set; }
        public byte? Development { get; set; }
        public string DevelopmentFurther { get; set; }
        public byte? Heart { get; set; }
        public byte? Hips { get; set; }
        public byte? Eyes { get; set; }
        public byte? Testes { get; set; }
        public byte? PhysicalGeneral { get; set; }
        public string DskLocomotor { get; set; }
        public string DskManipulative { get; set; }
        public string DskVisual { get; set; }
        public string DskHearingAndLanguage { get; set; }
        public string DskSpeechAndLanguage { get; set; }
        public string DskInteractiveSocial { get; set; }
        public string DskSelfCareSocial { get; set; }
        public string DskCognitive { get; set; }
        public string RecordStatus { get; set; }
        public byte? CoreComponent { get; set; }
        public virtual ChildExaminationGiven ChildExaminationGiven { get; set; }
    }
}
