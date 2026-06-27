import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';

// RainbowKit & Wagmi Imports
import '@rainbow-me/rainbowkit/styles.css';
import { getDefaultConfig, RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Define GenLayer Studionet chain
const studionetChain = {
  id: 61999,
  name: 'GenLayer Studionet',
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://studio.genlayer.com/api'] },
  },
  blockExplorers: {
    default: { name: 'GenExplorer', url: 'https://studio.genlayer.com' },
  },
};

// Define GenLayer Bradbury Testnet chain
const bradburyChain = {
  id: 4221,
  name: 'Genlayer Bradbury Testnet',
  nativeCurrency: { name: 'GEN Token', symbol: 'GEN', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://rpc-bradbury.genlayer.com'] },
  },
  blockExplorers: {
    default: { name: 'GenLayer Bradbury Explorer', url: 'https://explorer-bradbury.genlayer.com' },
  },
};

const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'your_walletconnect_project_id_here';

const config = getDefaultConfig({
  appName: 'GenShield On-Chain Auditor',
  projectId: projectId,
  chains: [studionetChain, bradburyChain],
  ssr: false,
});

const queryClient = new QueryClient();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={darkTheme({
          accentColor: '#0066ff',
          accentColorForeground: 'white',
          borderRadius: 'medium',
          overlayBlur: 'large',
        })}>
          <App />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  </StrictMode>,
);
