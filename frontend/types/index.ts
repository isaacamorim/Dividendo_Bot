// Tipos baseados no RETORNO REAL da API (snapshot é flat — sem MA200 nem
// objetos aninhados Valuation/Fundamentos/Tecnico; esses só existem no core).

export type Sinal = "BUY" | "HOLD" | "SELL";

export interface AtivoResult {
  ticker: string;
  data: string;
  preco: number | null;
  ma200: number | null;
  preco_justo: number | null;
  upside: number | null;
  dy: number | null;
  roe: number | null;
  pl: number | null;
  score: number | null;
  sinal: Sinal;
  estrategia: string;
  setor_perfil: string;
  div_estimado: number | null;
}

export interface ScanLatest {
  data: string;
  resultados: AtivoResult[];
  top5: AtivoResult[];
}

export interface HistoricoPonto {
  data: string;
  score: number | null;
  sinal: Sinal;
  preco: number | null;
  preco_justo: number | null;
  upside: number | null;
  dy: number | null;
  roe: number | null;
}

export interface HistoricoResponse {
  ticker: string;
  serie: HistoricoPonto[];
}

export interface Posicao {
  ticker: string;
  qtd: number;
  pm: number;
  preco_atual: number;
  investido: number;
  atual: number;
  lucro_cap: number;
  rentabilidade_pct: number;
  rent_total_pct: number;
  dividendos: number;
}

export interface CarteiraResumo {
  posicoes: Posicao[];
  total_investido: number;
  total_atual: number;
  lucro_capital: number;
  rentabilidade_pct: number;
  total_dividendos: number;
  rent_total_pct: number;
  alertas: string[];
}

export interface BacktestResult {
  ticker: string;
  periodo: string;
  origem: string;
  retorno_pct: number | null;
  cagr_pct: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  alpha_pct: number | null;
  win_rate_pct: number | null;
  n_trades: number | null;
  trades?: unknown[];
}
