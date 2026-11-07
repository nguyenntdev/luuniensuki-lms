export interface PricingTierInfo {
  key: string;
  name_vi: string;
  name_en: string;
  description_vi: string;
  description_en: string;
  base_price_vnd: number;
  billing_period: string;
  features_vi: string[];
  features_en: string[];
  is_popular?: boolean;
  calculator_supported?: boolean;
  anti_dark_pattern_notice: string;
}

export interface PricingExperimentConfigOut {
  experiment_key: string;
  variant_key: string;
  consent_required: boolean;
  consent_policy_version: string;
  consent_text_vi: string;
  consent_text_en: string;
  tiers: PricingTierInfo[];
  anti_abuse_notice: string;
}

export interface PricingCalculatorIn {
  tier_key: string;
  student_count: number;
  months_duration?: number;
  include_ai_tutor_credits?: boolean;
  include_vr360_interactive_lab?: boolean;
  include_teacher_training_pdu?: boolean;
}

export interface PricingCalculatorOut {
  tier_key: string;
  student_count: number;
  months_duration: number;
  base_subtotal_vnd: number;
  addons_subtotal_vnd: number;
  volume_discount_vnd: number;
  estimated_total_vnd: number;
  per_student_month_vnd: number;
  is_binding: boolean;
  revenue_recognized_vnd: number;
  disclaimer: string;
}

export interface PricingExperimentEventCreateIn {
  experiment_key?: string;
  variant_key?: string;
  tier_key: string;
  event_type: "tier_view" | "calculator_interaction" | "quote_inquiry" | "contract_sign_attempt" | "contract_accepted";
  has_experiment_consent: boolean;
  consent_version?: string;
  calculator_params?: Record<string, unknown>;
  client_metadata?: Record<string, unknown>;
  anonymous_session_id?: string;
}

export interface PricingExperimentEventOut {
  id: string;
  user_id?: string | null;
  experiment_key: string;
  variant_key: string;
  tier_key: string;
  event_type: string;
  has_experiment_consent: boolean;
  consent_version: string;
  is_paying_customer: boolean;
  revenue_impact_vnd: number;
  calculator_params?: Record<string, unknown> | null;
  created_at: string;
}

export interface PricingContractCreateIn {
  organization_name: string;
  school_id?: string | null;
  tier_key: string;
  variant_key?: string;
  student_seat_capacity: number;
  contract_value_vnd: number;
  terms_version?: string;
}

export interface PricingContractSignAcceptIn {
  confirmation_statement: string;
  signer_title: string;
  signer_legal_name: string;
  ip_address_masked?: string;
}

export interface PricingContractOut {
  id: string;
  contract_number: string;
  school_id?: string | null;
  organization_name: string;
  signer_user_id: string;
  tier_key: string;
  variant_key: string;
  contract_value_vnd: number;
  student_seat_capacity: number;
  status: string;
  terms_version: string;
  signed_at?: string | null;
  verification_hash?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PricingExperimentMetricsSummaryOut {
  experiment_key: string;
  total_tier_views: number;
  total_calculator_interactions: number;
  total_quote_inquiries: number;
  total_contract_attempts: number;
  signed_contracts_count: number;
  paying_customers_count: number;
  recognized_contract_revenue_vnd: number;
  unearned_calculator_projected_value_vnd: number;
  negative_abuse_verification: string;
}
