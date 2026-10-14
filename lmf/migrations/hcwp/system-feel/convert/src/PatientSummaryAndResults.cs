// Convert port of the approved extracted rules; see ../port.md for provenance.
using System;
using System.Linq;
using System.Collections.Generic;
namespace Hcwp.SystemFeel.Converted;
public static class Legacy {
public static string Name(ChildGeneral source)
        {
            return (string.IsNullOrEmpty(source.Title) ? string.Empty : source.Title + " ")
                                   + (string.IsNullOrEmpty(source.Surname) ? string.Empty : source.Surname + ", ")
                                   + (string.IsNullOrEmpty(source.Forename) ? string.Empty : source.Forename);
        }
public static string Address(ChildGeneral source)
        {
            var address = string.Empty; 

            if (!string.IsNullOrEmpty(source.Address1) && source.Address1 != "-")
                address += source.Address1 + ", ";
            if (!string.IsNullOrEmpty(source.Address2) && source.Address2 != "-")
                address += source.Address2 + ", ";
            if (!string.IsNullOrEmpty(source.Address3) && source.Address3 != "-")
                address += source.Address3 + ", ";
            if (!string.IsNullOrEmpty(source.Address4) && source.Address4 != "-")
                address += source.Address4 + ", ";
            if (!string.IsNullOrEmpty(source.Address5) && source.Address5 != "-")
                address += source.Address5 + ", ";
            if (!string.IsNullOrEmpty(source.Postcode) && source.Postcode != "-")
                address += source.Postcode;

            return address.TrimEnd().TrimEnd(',');
        }
public static string GetAge(DateTime dateOfBirth, DateTime? thresholdDate)
        {
            string age;

            var dateToCalculate = ReferenceClock.Now;

            if (thresholdDate.HasValue)
            {
                dateToCalculate = thresholdDate.Value;
            }

            var years = dateToCalculate.Year - dateOfBirth.Year;

            var months = (years*12) + (dateToCalculate.Month - dateOfBirth.Month);

            years = months / 12;

            if (years < 1)
            {
                if (months <= 3)
                {
                    var days = (int)(dateToCalculate - dateOfBirth).TotalDays;

                    if (days < 1)
                    {
                        age = "0 day";
                    }
                    else if (days == 1)
                    {
                        age = days + " day";
                    }
                    else if (days > 1 && days < 7)
                    {
                        age = days + " days";
                    }
                    else if (days < 14)
                    {
                        age = "1 week";
                    }
                    else
                    {
                        var weeks = (int)(dateToCalculate - dateOfBirth).TotalDays / 7;
                        age = weeks + " weeks";
                    }
                }
                else
                {
                    age = months + " months";
                }
            }
            else
            {
                months = months % 12;
                age = $"{years} Years {months} Months";
            }

            return age;
        }
public static string GetOrganisationValue(IEnumerable<ChildCentres> childCentres, IUnitOfWork uow)
        {
            string organisationValue;

            var locations = childCentres.FirstOrDefault(cc => cc.ChildLocationType == LookupsUtility.CENTRE_TYPES.HEALTH_AUTHORITY);
            if (locations != null)
            {
                if (locations.ChildLocations != null)
                {
                    var organisation = uow.Repository<ChildLocations>()
                        .AsNoTracking()
                        .SingleOrDefault(
                            cl => cl.Code == locations.ChildLocations.Organisation && cl.LocationTypes.Authority == "Y");

                    organisationValue = (organisation == null ? "-" : String.Join(", ", organisation.Code, organisation.Name));
                }
                else
                {
                    organisationValue = "-";
                }
            }
            else
            {
                organisationValue = "-";
            }

            return organisationValue;
        }
public static object School(ChildCentres source)
        {
            return source != null ? GetChildCentreText(source) : "-";
        }
private static object GetChildCentreText(ChildCentres childCentres)
        {
            return Resource.Format("CodeDescriptionFormat", childCentres.ChildLocationCode, childCentres.ChildLocations?.Name);
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
public static string SpanText(object value, string format, bool leaveBlankIfNull) { string text;
            if (value != null && !string.IsNullOrEmpty(value.ToString()))
            {
                text = format != null ? string.Format(format, value) : value.ToString();
            }
            else
            {
                text = leaveBlankIfNull ? string.Empty : "-";
            }


return text; }
}
public class AlertModel {
public string CurrentStatusCode {get;set;}
public List<string> ChildAlerts {get;set;} = new();
public bool ShowAlert => CurrentStatusCode == LookupsUtility.CurrentStatus_MovementOut || CurrentStatusCode == LookupsUtility.CurrentStatus_TransferredOut
                                 || CurrentStatusCode == LookupsUtility.CurrentStatus_Died || CurrentStatusCode == LookupsUtility.CurrentStatus_Stillbirth || ChildAlerts.Any();
}
public class LegacyDelegate {
public ResultService service;
public ResultTO ato;
public List<Row> listOfKdpExaminationResultDelegates;
private Row GetNewKdpExaminationResultDelegate(Row row) => row;
public void GetKdpResults(long clientId)
        {
            ato = service.GetKdpExamination(clientId);
            listOfKdpExaminationResultDelegates = ato.HcpExaminationResultToList.OrderByDescending(it => it.ExaminationDate).Select(GetNewKdpExaminationResultDelegate).ToList();
        }
}
public class ResultService {
public List<ChildExamination> entities;
public ResultTO GetKdpExamination(long clientId) {
var childExamination = entities
.Where(c => c.ClientId == clientId && c.ExaminationDescriptions.FkExamDescriptionType == ExamType.Kdp)
                    .OrderByDescending(c => c.ChildExaminationGiven.ExaminationDate)
                    .ToList();
return new ResultTO { HcpExaminationResultToList = childExamination.Select(c => c.Saved).ToList() };
}
}
