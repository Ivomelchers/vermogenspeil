import {
  FormControl,
  FormErrorMessage,
  FormHelperText,
  FormLabel,
  Input,
  type InputProps,
} from "@chakra-ui/react";

interface AuthFormFieldProps extends InputProps {
  label: string;
  error?: string;
  helperText?: string;
}

export default function AuthFormField({
  label,
  error,
  helperText,
  id,
  ...inputProps
}: AuthFormFieldProps) {
  const fieldId = id ?? inputProps.name;

  return (
    <FormControl isInvalid={Boolean(error)}>
      <FormLabel
        htmlFor={fieldId}
        fontSize="meta"
        fontWeight={500}
        letterSpacing="0.06em"
        textTransform="uppercase"
        color="ink.dim"
        mb={2}
      >
        {label}
      </FormLabel>
      <Input id={fieldId} variant="fiscal" {...inputProps} />
      {helperText && !error && (
        <FormHelperText color="ink.faint" fontSize="sm" mt={2}>
          {helperText}
        </FormHelperText>
      )}
      {error && <FormErrorMessage fontSize="sm">{error}</FormErrorMessage>}
    </FormControl>
  );
}
