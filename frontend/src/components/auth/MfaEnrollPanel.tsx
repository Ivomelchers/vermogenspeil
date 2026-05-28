import { FormEvent, useEffect, useState } from "react";
import { Box, Button, Code, Text, VStack } from "@chakra-ui/react";
import QRCode from "react-qr-code";

import {
  enrollAuthenticator,
  enrollAuthenticatorConfirm,
  type Auth0TokenResponse,
} from "../../api/auth";
import AuthAlert from "./AuthAlert";
import AuthFormField from "./AuthFormField";
import FiscalCard from "../common/FiscalCard";
import { getApiErrorMessage } from "../../utils/apiError";

interface MfaEnrollPanelProps {
  mfaToken: string;
  onSuccess: (tokens: Auth0TokenResponse) => Promise<void> | void;
  onCancel?: () => void;
}

export default function MfaEnrollPanel({
  mfaToken,
  onSuccess,
  onCancel,
}: MfaEnrollPanelProps) {
  const [enrollData, setEnrollData] = useState<{
    secret: string;
    barcode_uri: string;
    client_secret?: string;
  } | null>(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    setError("");
    enrollAuthenticator(mfaToken)
      .then((data) => setEnrollData(data))
      .catch(() => setError("2FA-setup starten mislukt. Probeer het opnieuw."))
      .finally(() => setIsLoading(false));
  }, [mfaToken]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!enrollData) return;

    setError("");
    setIsSubmitting(true);

    try {
      const tokens = await enrollAuthenticatorConfirm({
        mfa_token: mfaToken,
        otp: otp.trim(),
        binding_secret: enrollData.client_secret,
      });
      await onSuccess(tokens);
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Ongeldige verificatiecode."));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <FiscalCard p={6}>
        <Text color="ink.dim" fontSize="sm">
          QR-code voorbereiden...
        </Text>
      </FiscalCard>
    );
  }

  return (
    <FiscalCard p={6}>
      <VStack as="form" align="stretch" spacing={5} onSubmit={handleSubmit}>
        <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
          Installeer een authenticator-app (Google Authenticator, Microsoft Authenticator)
          en scan de QR-code of voer de geheime sleutel handmatig in.
        </Text>

        {error && <AuthAlert tone="error">{error}</AuthAlert>}

        {enrollData && (
          <>
            <Box
              p={4}
              bg="background"
              border="1px solid"
              borderColor="line.soft"
              borderRadius="sm"
              alignSelf="center"
            >
              <QRCode value={enrollData.barcode_uri} size={180} />
            </Box>
            <Box>
              <Text fontSize="xs" color="ink.dim" mb={2}>
                Geheime sleutel (handmatig)
              </Text>
              <Code p={3} display="block" whiteSpace="pre-wrap" wordBreak="break-all">
                {enrollData.secret}
              </Code>
            </Box>
          </>
        )}

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
