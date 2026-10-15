export const API_BASE = "/api/v1";

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface FailurePrediction {
  failure_type: string;
  probability: number;
  risk_level: string;
  description: string;
  evidence: string[];
  mitigation: string;
}

export interface ComponentRecommendation {
  component_name: string;
  category: string;
  recommended: boolean;
  reason: string;
  risk_score: number;
  dependencies_satisfied: boolean;
  conflicts: string[];
}

export interface AnalysisResult {
  recipe_name: string;
  target_build: string;
  analyzed_at: string;
  overall_risk: string;
  risk_score: number;
  failure_predictions: FailurePrediction[];
  component_recommendations: ComponentRecommendation[];
  warnings: string[];
  metadata: Record<string, unknown>;
}

export interface AnalyzeRecipeResponse {
  analysis: AnalysisResult;
}

export interface ComponentInfo {
  name: string;
  category: string;
  description: string;
  size_mb: number;
  dependencies: string[];
  conflicts: string[];
  safe_to_remove: boolean;
  min_build: string;
  max_build: string;
  provides: string[];
  required_by: string[];
}

export interface ComponentDatabaseResponse {
  components: ComponentInfo[];
  target_build: string;
  total_count: number;
}

export interface ValidationIssue {
  severity: string;
  code: string;
  message: string;
  xpath: string;
  line: number;
  fix_suggestion: string;
}

export interface ValidateAutounattendResponse {
  valid: boolean;
  issues: ValidationIssue[];
  passes_found: string[];
  components_referenced: string[];
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/healthz`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function analyzeRecipe(
  recipe: Record<string, unknown>,
  targetBuild: string
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/analyze/recipe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe, target_build: targetBuild }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data: AnalyzeRecipeResponse = await response.json();
  return data.analysis;
}

export async function getComponentRecommendations(
  targetBuild: string,
  categories?: string[],
  includeUnsafe = false
): Promise<ComponentRecommendation[]> {
  const response = await fetch(`${API_BASE}/analyze/advisor/components`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_build: targetBuild, categories, include_unsafe: includeUnsafe }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  return data.components;
}

export async function getComponentDatabase(targetBuild: string): Promise<ComponentDatabaseResponse> {
  const response = await fetch(`${API_BASE}/analyze/advisor/database?target_build=${targetBuild}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function validateAutounattend(xml: string): Promise<ValidateAutounattendResponse> {
  const response = await fetch(`${API_BASE}/validate/autounattend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ xml }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}