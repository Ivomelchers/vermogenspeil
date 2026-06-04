import { Text } from "@chakra-ui/react";

import FiscalCard from "../common/FiscalCard";
import SectionHeader from "../common/SectionHeader";

/** Totale transactiekosten per platform — MVP-placeholder tot fee-tracking live is. */
export default function PlatformFeesPlaceholder() {
  return (
    <>
      <SectionHeader
        title="Totale transactiekosten"
        kicker="per platform · binnenkort"
      />
      <FiscalCard elevated p={5}>
        <Text fontSize="sm" color="ink.dim" lineHeight={1.7}>
          Hier komt een overzicht van transactie- en beheerkosten per gekoppeld
          platform. Die gegevens halen we uit uw import; de uitgesplitste weergave
          volgt in een volgende versie.
        </Text>
      </FiscalCard>
    </>
  );
}
