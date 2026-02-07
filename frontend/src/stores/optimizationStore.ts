import { create } from 'zustand';
import type {
  OptimizationMethod,
  ConstraintType,
  OptimizationResponse,
  EfficientFrontierPoint,
} from '../types';
import * as api from '../api/api';

interface OptimizationState {
  // Result state
  result: OptimizationResponse | null;
  frontier: EfficientFrontierPoint[];

  // Parameters
  method: OptimizationMethod;
  minWeight: number;
  maxWeight: number;
  riskFreeRate: number;
  cvarAlpha: number;
  riskAversion: number;
  expRiskAversion: number;
  constraintType: ConstraintType;
  maxVolatility: number;
  maxCvar: number;

  // Loading
  isOptimizing: boolean;
  isFrontierLoading: boolean;

  // Actions
  setMethod: (m: OptimizationMethod) => void;
  setMinWeight: (w: number) => void;
  setMaxWeight: (w: number) => void;
  setRiskFreeRate: (r: number) => void;
  setCvarAlpha: (a: number) => void;
  setRiskAversion: (r: number) => void;
  setExpRiskAversion: (r: number) => void;
  setConstraintType: (t: ConstraintType) => void;
  setMaxVolatility: (v: number) => void;
  setMaxCvar: (c: number) => void;
  runOptimization: () => Promise<void>;
  fetchFrontier: () => Promise<void>;
  reset: () => void;
}

const DEFAULTS = {
  method: 'Maximum Sharpe Ratio' as OptimizationMethod,
  minWeight: 0.0,
  maxWeight: 1.0,
  riskFreeRate: 0.02,
  cvarAlpha: 0.05,
  riskAversion: 1.0,
  expRiskAversion: 0.5,
  constraintType: 'volatility' as ConstraintType,
  maxVolatility: 0.15,
  maxCvar: 0.25,
};

export const useOptimizationStore = create<OptimizationState>((set, get) => ({
  result: null,
  frontier: [],
  isOptimizing: false,
  isFrontierLoading: false,
  ...DEFAULTS,

  setMethod: m => set({ method: m }),
  setMinWeight: w => set({ minWeight: w }),
  setMaxWeight: w => set({ maxWeight: w }),
  setRiskFreeRate: r => set({ riskFreeRate: r }),
  setCvarAlpha: a => set({ cvarAlpha: a }),
  setRiskAversion: r => set({ riskAversion: r }),
  setExpRiskAversion: r => set({ expRiskAversion: r }),
  setConstraintType: t => set({ constraintType: t }),
  setMaxVolatility: v => set({ maxVolatility: v }),
  setMaxCvar: c => set({ maxCvar: c }),

  runOptimization: async () => {
    const s = get();
    set({ isOptimizing: true });
    try {
      const result = await api.optimizePortfolio({
        method: s.method,
        min_weight: s.minWeight,
        max_weight: s.maxWeight,
        risk_free_rate: s.riskFreeRate,
        cvar_alpha: s.cvarAlpha,
        risk_aversion: s.riskAversion,
        exp_risk_aversion: s.expRiskAversion,
        constraint_type: s.constraintType,
        max_volatility: s.maxVolatility,
        max_cvar: s.maxCvar,
      });
      set({ result, isOptimizing: false });
    } catch {
      set({ isOptimizing: false });
      throw new Error('Optimization failed');
    }
  },

  fetchFrontier: async () => {
    const s = get();
    set({ isFrontierLoading: true });
    try {
      const frontier = await api.getEfficientFrontier({
        min_weight: s.minWeight,
        max_weight: s.maxWeight,
        n_points: 25,
        risk_free_rate: s.riskFreeRate,
      });
      set({ frontier, isFrontierLoading: false });
    } catch {
      set({ isFrontierLoading: false });
    }
  },

  reset: () => set({ ...DEFAULTS, result: null, frontier: [] }),
}));