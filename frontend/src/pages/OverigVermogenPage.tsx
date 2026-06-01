import { useEffect, useState } from "react";
import { Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { getTaxYearContext } from "../api/tax";
import FiscalDisclaimer from "../components/common/FiscalDisclaimer";
import FiscalNote from "../components/common/FiscalNote";
import OverigVermogenWorkspace from "../components/tax/OverigVermogenWorkspace";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { relevantTaxYear } from "../utils/taxYear";

export default function OverigVermogenPage() {
  const [taxYear, setTaxYear] = useState(relevantTaxYear());

  useEffect(() => {
    void getTaxYearContext().then((ctx) => setTaxYear(ctx.relevant_tax_year));
  }, []);

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker={`Overig vermogen · ${taxYear}`}
          title={
            <>
              Vastgoed, bank & <Text as="em">schulden</Text>
            </>
          }
          subtitle="Voeg vastgoed, schulden en banktegoeden toe. De gegevens worden direct meegenomen in uw Box 3-berekening op de belastingpositie."
        />
      </MotionSection>

      <MotionSection>
        <FiscalDisclaimer>
          <strong>Hoe werkt dit?</strong> Banktegoeden tellen mee als B, schulden als S (met
          schuldendrempel), vastgoed als overige bezittingen. Na wijzigingen: leg peildatum opnieuw
          vast voor een actuele forfaitaire berekening.
        </FiscalDisclaimer>
      </MotionSection>

      <MotionSection>
        <FiscalNote>
          Tip: na opslaan ga naar{" "}
          <Text as={RouterLink} to="/belasting" color="azure.500" fontStyle="normal" fontWeight={500}>
            belastingpositie
          </Text>{" "}
          en leg uw peildatum opnieuw vast.
        </FiscalNote>
      </MotionSection>

      <MotionSection>
        <OverigVermogenWorkspace taxYear={taxYear} />
      </MotionSection>
    </PageShell>
  );
}
