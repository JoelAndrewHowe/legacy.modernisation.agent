// Extracted bundle file 18; see extract.py and README.md.
using System;
using System.Diagnostics;
using System.Runtime.Serialization;

namespace Orvex.TransferObjects
{
    public enum TypeOfLookup
    {
        AllExams,
        Examiners,
        ExaminerByPrimaryKeyKdp,
        ExamLocationTypeKdp,
        ExamNotExaminedReasonKdp,
        Locations
    }

    [DataContract]
    [DebuggerDisplay("Code={Code}, Description={Description}")]
    public class LookupsSubTO : AbstractTO
    {
        public enum LOOKUPSubTO_ENUM
        {
            CODE, DESCRIPTION, ACTIVE_TO, ACTIVE_FROM, TYPE, LINKED_ORGANISATION, SUB_TYPE, ADD1, ADD2, ADD3, ADD4, ADD5, POSTCODE, TELEPHONE, ADDRESS_LINES, USED_CODE
        }

        public override Array getEnumValues()
        {
            return Enum.GetValues(typeof(LOOKUPSubTO_ENUM));
        }

        [DataMember]
        public string Code
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.CODE); }
            set { setProperty(LOOKUPSubTO_ENUM.CODE, value); }
        }

        [DataMember]
        public string Description
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.DESCRIPTION); }
            set { setProperty(LOOKUPSubTO_ENUM.DESCRIPTION, value); }
        }

        [DataMember]
        public DateTime? ActiveTo
        {
            get { return (DateTime?)getProperty(LOOKUPSubTO_ENUM.ACTIVE_TO); }
            set { setProperty(LOOKUPSubTO_ENUM.ACTIVE_TO, value); }
        }

        [DataMember]
        public DateTime? ActiveFrom
        {
            get { return (DateTime?)getProperty(LOOKUPSubTO_ENUM.ACTIVE_FROM); }
            set { setProperty(LOOKUPSubTO_ENUM.ACTIVE_FROM, value); }
        }

        [DataMember]
        public string Type
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.TYPE); }
            set { setProperty(LOOKUPSubTO_ENUM.TYPE, value); }
        }

        [DataMember]
        public string LinkedOrganisation
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.LINKED_ORGANISATION); }
            set { setProperty(LOOKUPSubTO_ENUM.LINKED_ORGANISATION, value); }
        }

        [DataMember]
        public string SubType
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.SUB_TYPE); }
            set { setProperty(LOOKUPSubTO_ENUM.SUB_TYPE, value); }
        }

        [DataMember]
        public string Address1
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADD1); }
            set { setProperty(LOOKUPSubTO_ENUM.ADD1, value); }
        }

        [DataMember]
        public string Address2
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADD2); }
            set { setProperty(LOOKUPSubTO_ENUM.ADD2, value); }
        }

        [DataMember]
        public string Address3
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADD3); }
            set { setProperty(LOOKUPSubTO_ENUM.ADD3, value); }
        }

        [DataMember]
        public string Address4
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADD4); }
            set { setProperty(LOOKUPSubTO_ENUM.ADD4, value); }
        }

        [DataMember]
        public string Address5
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADD5); }
            set { setProperty(LOOKUPSubTO_ENUM.ADD5, value); }
        }

        [DataMember]
        public string Postcode
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.POSTCODE); }
            set { setProperty(LOOKUPSubTO_ENUM.POSTCODE, value); }
        }

        [DataMember]
        public string Telephone
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.TELEPHONE); }
            set { setProperty(LOOKUPSubTO_ENUM.TELEPHONE, value); }
        }

        [DataMember]
        public string AddressLines
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.ADDRESS_LINES); }
            set { setProperty(LOOKUPSubTO_ENUM.ADDRESS_LINES, value); }
        }

        [DataMember]
        public string UsedCode
        {
            get { return (string)getProperty(LOOKUPSubTO_ENUM.USED_CODE); }
            set { setProperty(LOOKUPSubTO_ENUM.USED_CODE, value); }
        }

        [DataMember]
        public string ShortDescription { get; set; }

        public string ExaminerType { get; set; }

        public override string ToString()
        {
            return string.Format("{0} - {1}", Code, Description);
        }
    }
}
