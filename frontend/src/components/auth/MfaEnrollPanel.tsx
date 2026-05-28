import { FormEvent, useState } from "react";
import { Box, Button, Code, Text, VStack } from "@chakra-ui/react";
import QRCode from "react-qr-code";

import { verifyTwoFactorSetup, type TwoFactorSetupResponse } from "../../api/auth";
import AuthAlert from "./AuthAlert";
import AuthFormField from "./AuthFormField";
import FiscalCard from "../common/FiscalCard";
import { getApiErrorMessage } from "../../utils/apiError";

interface MfaEnrollPanelProps {
  setupData: TwoFactorSetupResponse;
  onSuccess: (backupCodes: string[]) => Promise<void> | void;
  onCancel?: () => void;
}

export default function MfaEnrollPanel({
  setupData,
  onSuccess,
  onCancel,
}: MfaEnrollPanelProps) {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const result = await verifyTwoFactorSetup(otp.trim());
      await onSuccess(result.backup_codes);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Ongeldige verificatiecode."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <FiscalCard p={6}>
      <VStack as="form" align="stretch" spacing={5} onSubmit={handleSubmit}>
        <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
          Installeer een authenticator-app (Google Authenticator, Microsoft Authenticator)
          en scan de QR-code of voer de geheime sleutel handmatig in.
        </Text>

        {error && <AuthAlert tone="error">{error}</AuthAlert>}

        <Box
          p={4}
          bg="background"
          border="1px solid"
          borderColor="line.soft"
          borderRadius="sm"
          alignSelf="center"
        >
          <QRCode value={setupData.barcode_uri} size={180} />
        </Box>
        <Box>
          <Text fontSize="xs" color="ink.dim" mb={2}>
            Geheime sleutel (handmatig)
          </Text>
          <Code p={3} display="block" whiteSpace="pre-wrap" wordBreak="break-all">
            {setupData.secret}
          </Code>
        </Box>

        <AuthFormField
          label="Verificatiecode uit app"
          name="otp"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          value={otp}
          onChange={(event) => setOtp(event.target.value)}
          isRequired
        />

        <Button type="submit" variant="fiscal" w="full" isLoading={isSubmitting}>
          2FA activeren
        </Button>

        {onCancel && (
          <Button type="button" variant="fiscalOutline" w="full" onClick={onCancel}>
            Annuleren
          </Button>
        )}
      </VStack>
    </FiscalCard>
  );
}
