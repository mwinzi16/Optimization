import { create } from 'zustand';
import type { AssetInfo } from '../types';
import * as api from '../api/api';

interface DataState {
  assets: AssetInfo[];
  scenarioCount: number;
  assetCount: number;
  isDataLoaded: boolean;
  isUploading: boolean;
  dataSource: string;

  fetchAssets: () => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  resetData: () => Promise<void>;
}

export const useDataStore = create<DataState>((set) => ({
  assets: [],
  scenarioCount: 0,
  assetCount: 0,
  isDataLoaded: false,
  isUploading: false,
  dataSource: 'sample',

  fetchAssets: async () => {
    const assets = await api.fetchAssets();
    set({
      assets,
      assetCount: assets.length,
      isDataLoaded: true,
    });
  },

  uploadFile: async (file: File) => {
    set({ isUploading: true });
    try {
      const resp = await api.uploadFile(file);
      set({
        isUploading: false,
        assetCount: resp.n_assets,
        scenarioCount: resp.n_scenarios,
        dataSource: file.name,
      });
      // Re-fetch assets after upload
      const assets = await api.fetchAssets();
      set({ assets, isDataLoaded: true });
    } catch {
      set({ isUploading: false });
      throw new Error('Upload failed');
    }
  },

  resetData: async () => {
    await api.resetData();
    const assets = await api.fetchAssets();
    set({
      assets,
      assetCount: assets.length,
      isDataLoaded: true,
      dataSource: 'sample',
    });
  },
}));