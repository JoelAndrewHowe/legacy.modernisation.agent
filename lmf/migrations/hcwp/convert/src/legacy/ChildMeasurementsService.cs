using System;
using System.Collections.Generic;
using System.Linq;
using Orvex.TransferObjects;
using HLX.BusinessTier.Common.Util;
using Orvex.DomainModel;
using Orvex.Model;
using Orvex.Services;
using Orvex.Services.Internal;

namespace Orvex.Business
{
    
    public class ChildMeasurementsService : IChildMeasurementsService
    {
        private readonly Func<IUnitOfWork> unitOfWorkFactory;

        public ChildMeasurementsService(Func<IUnitOfWork> unitOfWorkFactory)
        {
            this.unitOfWorkFactory = unitOfWorkFactory;
        }

        public decimal? CalculateBmi(decimal height, decimal weight)
        {
            var result = Math.Round(weight / ((height / 100) * (height / 100)), 2);
            decimal? roundedBmi = Convert.ToDecimal(result);
            if (roundedBmi > (decimal)99.99)
                roundedBmi = (decimal)99.99;

            return roundedBmi;
        }

        public List<ChildMeasurementsRange> GetPrescribedRanges()
        {
            var generalOptions = getGeneralOptions();
            return new List<ChildMeasurementsRange>
            {
                new ChildMeasurementsRange
                {
                    MeasurementType = "BMI",
                    UpperBound = (double)generalOptions.HBmiIndex,
                    LowerBound = (double)generalOptions.LBmiIndex,
                }
            };
        }

        public List<ChildMeasurementsRange> GetExpectedRanges(string gender, DateTime dateOfBirth, DateTime dateOfExamination)
        {
            var ageInDays = dateOfBirth.DaysBetween(dateOfExamination);

            var centileBands = getCentileBands(ageInDays, gender);

            return centileBands
                .GroupBy(cb => cb.MeasurementType)
                .Select(cb => new ChildMeasurementsRange
                {
                    MeasurementType = cb.Key,
                    UpperBound = cb.Max(b => b.Lower),
                    LowerBound = cb.Min(b => b.Upper)
                }).ToList();
        }

        private IEnumerable<DeviationsCentile> getCentileBands(int ageInDays, string gender)
        {
            using (var uow = unitOfWorkFactory())
            {
                return uow.Repository<DeviationsCentile>().Where(d => d.Age == ageInDays && d.Gender == gender).ToList();
            }
        }

        private SystemGeneralOptions getGeneralOptions()
        {
            using (var uow = unitOfWorkFactory())
            {
                return uow.Repository<SystemGeneralOptions>().First();
            }
        }
    }
}
