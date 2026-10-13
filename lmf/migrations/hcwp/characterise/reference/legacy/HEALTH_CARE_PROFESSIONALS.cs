// Extracted bundle file 83; see extract.py and README.md.
using Orvex.Model.Extensions;
using System;
using System.Collections.Generic;

namespace Orvex.Model
{
    public class HealthCareProfessionals : IActiveDateRange
    {
        public HealthCareProfessionals()
        {
            ChildExaminationGiven = new List<ChildExaminationGiven>();
        }

        public string Code { get; set; }
        public string StaffType { get; set; }
        public string Name1 { get; set; }
        public string Name2 { get; set; }
        public DateTime? ActiveFrom { get; set; }
        public DateTime? ActiveTo { get; set; }
        public string RecordStatus { get; set; }
        public virtual ICollection<ChildExaminationGiven> ChildExaminationGiven { get; set; }

    }
}
