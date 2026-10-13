using Orvex.TransferObjects;

namespace Hcwp.Domain;

public static class Kd03Scope
{
    public const string Code = "KD03";
    public static void EnsureNewResult(long selectedPatient, KdpExaminationResultTO draft)
    {
        if (draft.ExaminationCode != Code) throw new ArgumentException("UnsupportedContact");
        if (draft.ClientId != selectedPatient || draft.PkChildExaminationId != 0 || draft.ChildMeasurementId != 0)
            throw new ArgumentException("Only new results for the selected patient are supported.");
    }
}
