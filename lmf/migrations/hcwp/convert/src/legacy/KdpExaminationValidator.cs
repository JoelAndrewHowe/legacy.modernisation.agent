// Extracted bundle file 27; see extract.py and README.md.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Orvex.Messages.Faults;
using Orvex.TransferObjects;
using static Orvex.Resources.Resources;

// ReSharper disable once CheckNamespace
namespace Orvex.Business.Validation
{
    public class KdpExaminationValidator
    {
        private const string YesValue = "Y";

        private const decimal HeightMinValue = 0;
        private const decimal WeightMinValue = 0;
        private const decimal HeadCircumferenceMinValue = 0;

        private const decimal HeightMaxValue = 1000;
        private const decimal WeightMaxValue = 1000;
        private const decimal HeadCircumferenceMaxValue = 1000;

        private readonly string kdpInvalidHeightMessage = string.Format(InvalidHeightMessage, HeightMinValue, HeightMaxValue);
        private readonly string kdpInvalidWeightMessage = string.Format(InvalidWeightMessage, WeightMinValue, WeightMaxValue);
        private readonly string kdpInvalidHeadCircumferenceMessage = string.Format(InvalidHeadCircumferenceMessage, HeadCircumferenceMinValue, HeadCircumferenceMaxValue);
        


        public void ValidateNewExamCode(string examCode, List<LookupsSubTO> validExaminations)
        {
            if (string.IsNullOrEmpty(examCode))
                return;

            if (validExaminations.All(ex => ex.Code != examCode))
            {
                throw ValidationFault.Default(KdpInvalidExamCodeMessage, InvalidExamCodePrompt);
            }
        }

        public void ValidateExamCodeForDuplicates(List<KdpExaminationResultTO> existingResults, string examCode, long resultId)
        {
            if (string.IsNullOrEmpty(examCode))
                return;

            if (existingResults.Any(r => r.ExaminationCode == examCode && r.PkChildExaminationId != resultId))
            {
                throw ValidationWarningFault.Default(KdpDuplicateExamCodeMessage, DuplicateExamCodePrompt);
            }
        }

        public void ValidateExamCodeForDate(List<KdpExaminationResultTO> existingResults, long id, string examCode, DateTime examDate)
        {
            if (ResultAlreadyExistsForCodeAndDate(existingResults, id, examCode, examDate))
            {
                throw ValidationFault.Default(KdpResultAlreadyEnteredMessage, DuplicateExamCodePrompt);
            }
        }

        private static bool ResultAlreadyExistsForCodeAndDate(List<KdpExaminationResultTO> existingResults, long id, string examCode, DateTime examDate)
        {
            if (existingResults == null)
                return false;

            return existingResults.Any(r => r.PkChildExaminationId != id && r.ExaminationCode == examCode && r.ExaminationDate.Date == examDate.Date);
        }

        public void ValidateKdpConsent(long clientId, bool hasConsent)
        {
            if (!hasConsent)
            {
                throw ValidationWarningFault.Default(string.Format(NoConsentMessage, clientId), ChildHasNoConsentPrompt);
            }
        }

        public void ValidateExaminationDate(DateTime enteredDate, DateTime dateOfBirth, DateTime? dateOfDeath)
        {
            if (IsExaminationDateInTheFuture(enteredDate))
            {
                throw ValidationFault.Default(FutureExamDateMessage, InvalidExamDatePrompt);
            }

            if (!IsExaminationDateAfterBirthDate(enteredDate, dateOfBirth))
            {
                throw ValidationFault.Default(ExamDateBeforeDobMessage, InvalidExamDatePrompt);
            }

            if (!IsExaminationDateBeforeDeathDate(enteredDate, dateOfDeath))
            {
                throw ValidationFault.Default(ExamDateAfterDeathMessage, InvalidExamDatePrompt);
            }
        }

        private static bool IsExaminationDateInTheFuture(DateTime enteredDate)
        {
            return enteredDate.Date > ReferenceClock.Today;
        }

        private static bool IsExaminationDateAfterBirthDate(DateTime enteredDate, DateTime dateOfBirth)
        {
            return enteredDate >= dateOfBirth;
        }

        private static bool IsExaminationDateBeforeDeathDate(DateTime enteredDate, DateTime? dateOfDeath)
        {
            return !dateOfDeath.HasValue || enteredDate <= dateOfDeath;
        }

        public void ValidateHeight(decimal? height)
        {
            if (!ValueIsNullOrWithinRange(height, HeightMinValue, HeightMaxValue))
            {
                throw ValidationFault.Default(kdpInvalidHeightMessage, InvalidHeightPrompt);
            }
        }

        public void ValidateWeight(decimal? weight)
        {
            if (!ValueIsNullOrWithinRange(weight, WeightMinValue, WeightMaxValue))
            {
                throw ValidationFault.Default(kdpInvalidWeightMessage, InvalidWeightPrompt);
            }
        }

        public void ValidateHeadCircumference(decimal headCircumference)
        {
            if (headCircumference <= 0)
            {
                throw ValidationFault.Default(HeadCircumferenceMinusNumberErrorMessage, InvalidHeadCircumferencePrompt);
            }
            if (headCircumference >= 100)
            {
                throw ValidationFault.Default(HeadCircumferenceInvalidFormatMessage, InvalidHeadCircumferencePrompt);

            }
            if (!ValueIsNullOrWithinRange(headCircumference, HeadCircumferenceMinValue, HeadCircumferenceMaxValue))
            {
                throw ValidationFault.Default(kdpInvalidHeadCircumferenceMessage, InvalidHeadCircumferencePrompt);
            }
        }

        private static bool ValueIsNullOrWithinRange(decimal? nullableValue, decimal minValue, decimal maxValue)
        {
            return !nullableValue.HasValue || (nullableValue.Value > minValue && nullableValue.Value < maxValue);
        }

        private static bool NoResults(KdpExaminationResultTO results)
        {
            return results.Height == null &&
                   results.Weight == null &&
                   results.HeadCircumference == null &&
                   results.DomesticViolenceConcern == null &&
                   results.RskResponsiveParenting == null &&
                   results.RskEngagement == null &&
                   results.RskSocioFactors == null &&
                   results.RskFamilyHealth == null &&
                   results.RskFamilySupport == null &&
                   results.Development == null &&
                   results.EvidenceOfXgm == null &&
                   results.Hips == null &&
                   results.Heart == null &&
                   results.Eyes == null &&
                   results.Testes == null &&
                   string.IsNullOrEmpty(results.DskCognitive) &&
                   string.IsNullOrEmpty(results.DskHearingAndLanguage) &&
                   string.IsNullOrEmpty(results.DskInteractiveSocial) &&
                   string.IsNullOrEmpty(results.DskLocomotor) &&
                   string.IsNullOrEmpty(results.DskManipulative) &&
                   string.IsNullOrEmpty(results.DskSelfCareSocial) &&
                   string.IsNullOrEmpty(results.DskSpeechAndLanguage) &&
                   string.IsNullOrEmpty(results.DskVisual) &&
                   string.IsNullOrEmpty(results.ReceivingBoostSchemeService) &&
                   string.IsNullOrEmpty(results.LookedAfterChild) &&
                   string.IsNullOrEmpty(results.OnChildProtectionRegister) &&
                   string.IsNullOrEmpty(results.OnwardReferralsMade) &&
                   string.IsNullOrEmpty(results.RskCompleted) &&
                   string.IsNullOrEmpty(results.DevelopmentFurther);
        }

        public void ValidateOnSave(KdpExaminationResultTO newExaminationResult, DateTime dateOfBirth, DateTime? dateOfDeath, List<KdpExaminationResultTO> existingResults = null)
        {
            var errorMessage = new StringBuilder();

            byte count = 1;

            if (string.IsNullOrEmpty(newExaminationResult.ExaminationCode))
            {
                errorMessage.Append($"{count++}: {NoExamCodeMessage}{Environment.NewLine}");
            }

            if (newExaminationResult.ExaminationDate == DateTime.MinValue)
            {
                errorMessage.Append($"{count++}: {NoExamDateMessage}{Environment.NewLine}");
            }
            else if (IsExaminationDateInTheFuture(newExaminationResult.ExaminationDate))
            {
                errorMessage.Append($"{count++}: {FutureExamDateMessage}{Environment.NewLine}");
            }
            else if (!IsExaminationDateAfterBirthDate(newExaminationResult.ExaminationDate, dateOfBirth))
            {
                errorMessage.Append($"{count++}: {ExamDateBeforeDobMessage}{Environment.NewLine}");
            }
            else if (!IsExaminationDateBeforeDeathDate(newExaminationResult.ExaminationDate, dateOfDeath))
            {
                errorMessage.Append($"{count++}: {ExamDateAfterDeathMessage}{Environment.NewLine}");
            }

            if (!ValueIsNullOrWithinRange(newExaminationResult.Height, HeightMinValue, HeightMaxValue))
            {
                errorMessage.Append($"{count++}: {kdpInvalidHeightMessage}{Environment.NewLine}");
            }

            if (!ValueIsNullOrWithinRange(newExaminationResult.Weight, WeightMinValue, WeightMaxValue))
            {
                errorMessage.Append($"{count++}: {kdpInvalidWeightMessage}{Environment.NewLine}");
            }

            if (!ValueIsNullOrWithinRange(newExaminationResult.HeadCircumference, HeadCircumferenceMinValue, HeadCircumferenceMaxValue))
            {
                errorMessage.Append($"{count++}: {kdpInvalidHeadCircumferenceMessage}{Environment.NewLine}");
            }

            if (string.IsNullOrEmpty(newExaminationResult.ReasonNotExamined))
            {
                if (newExaminationResult.Reschedule == YesValue)
                {
                    errorMessage.Append($"{count++}: {RescheduleOnlyIfNotExaminedMessage}{Environment.NewLine}");
                }

                if (NoResults(newExaminationResult))
                {
                    errorMessage.Append($"{count++}: {NoResultsEnteredMessage}{Environment.NewLine}");
                }
            }
            else
            {
                if (!NoResults(newExaminationResult))
                {
                    errorMessage.Append($"{count++}: {ResultsRecordedButNotExamined}{Environment.NewLine}");
                }
            }

            if (ResultAlreadyExistsForCodeAndDate(existingResults, newExaminationResult.PkChildExaminationId, newExaminationResult.ExaminationCode, newExaminationResult.ExaminationDate))
            {
                errorMessage.Append($"{count}: {KdpResultAlreadyEnteredMessage}{Environment.NewLine}");
            }

            if (errorMessage.Length > 0)
            {
                throw ValidationFault.Default(errorMessage.ToString(), ValidationErrorsPrompt);
            }
        }
    }
}
