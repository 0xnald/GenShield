import React, { useState, useEffect, useRef } from 'react';
import { createClient, createAccount } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { 
  Shield, Play, Key, Wallet, Terminal, 
  FileCode, Award, AlertCircle, CheckCircle, 
  RefreshCw, ClipboardCheck, ArrowUpRight
} from 'lucide-react';

const SAMPLE_CODE = `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class MyContract(gl.Contract):
    value: u256

    def __init__(self, value: u256):
        self.value = value

    @gl.public.write
    def update_value(self, new_value: u256) -> None:
        self.value = new_value

    @gl.public.view
    def get_value(self) -> u256:
        return self.value
`;

function App() {
  const [connectionType, setConnectionType] = useState('wallet');
  const [walletAddress, setWalletAddress] = useState('');
  const [privateKey, setPrivateKey] = useState('');
  const [contractAddress, setContractAddress] = useState('0x5006f4C1d2201FF849EF0A1C664F4Ede300edbB2');
  const [contractName, setContractName] = useState('MySmartContract');
  const [code, setCode] = useState(SAMPLE_CODE);
  const [logs, setLogs] = useState([]);
  const [isAuditing, setIsAuditing] = useState(false);
  const [certificate, setCertificate] = useState(null);
  const [lineCount, setLineCount] = useState(1);
  const terminalEndRef = useRef(null);

  // Auto scroll terminal logs
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Update line numbers count
  useEffect(() => {
    const lines = code.split('\n').length;
    setLineCount(lines || 1);
  }, [code]);

  const addLog = (text, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { text, type, time }]);
  };

  const connectWallet = async () => {
    if (!window.ethereum) {
      addLog("Wallet connection failed: MetaMask/Rabby not detected", "error");
      alert("Please install an EVM-compatible browser wallet like MetaMask or Rabby first.");
      return;
    }
    try {
      addLog("Requesting wallet connection...", "info");
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      setWalletAddress(accounts[0]);
      addLog(`Wallet connected: ${accounts[0]}`, "success");
    } catch (err) {
      addLog(`Wallet connection error: ${err.message}`, "error");
    }
  };

  const handleAudit = async () => {
    if (!contractAddress) {
      alert("Please enter the GenShield contract address.");
      return;
    }
    
    setIsAuditing(true);
    setLogs([]);
    setCertificate(null);
    
    addLog("Initializing audit workflow...", "info");

    try {
      let client;
      
      if (connectionType === 'wallet') {
        if (!walletAddress) {
          addLog("Wallet is not connected. Attempting auto-connection...", "warning");
          if (!window.ethereum) {
            throw new Error("No browser wallet extension found.");
          }
          const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
          setWalletAddress(accounts[0]);
        }
        
        addLog(`Creating GenLayer client using injected provider (wallet: ${walletAddress || 'pending'})...`, "info");
        client = createClient({
          chain: studionet,
          account: walletAddress || window.ethereum.selectedAddress,
          provider: window.ethereum
        });
      } else {
        if (!privateKey) {
          throw new Error("Please enter a private key hex to sign transaction.");
        }
        
        // Ensure private key has 0x prefix if required, or validate it
        let cleanKey = privateKey.trim();
        if (!cleanKey.startsWith('0x') && cleanKey.length === 64) {
          cleanKey = '0x' + cleanKey;
        }
        
        addLog("Generating local account signer from private key...", "info");
        const account = createAccount(cleanKey);
        addLog(`Signer generated for: ${account.address}`, "success");
        
        client = createClient({
          chain: studionet,
          account: account
        });
      }

      addLog(`Preparing to call 'submit_audit' on contract: ${contractAddress}`, "info");
      
      // Calculate SHA-256 locally to log it
      const encoder = new TextEncoder();
      const codeBytes = encoder.encode(code);
      const hashBuffer = await crypto.subtle.digest('SHA-256', codeBytes);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const codeHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      addLog(`Calculated local code hash: ${codeHash}`, "sys");

      const fee = 1000n; // 1000 Wei audit fee
      addLog(`Submitting transaction with paid fee value: ${fee.toString()} Wei`, "info");
      
      const txHash = await client.writeContract({
        address: contractAddress,
        functionName: "submit_audit",
        args: [contractName, code],
        value: fee
      });
      
      addLog(`On-chain transaction submitted!`, "success");
      addLog(`Tx Hash: ${txHash}`, "sys");
      addLog("Awaiting validator democratic consensus (LLM runs & equivalence check)...", "warning");

      const receipt = await client.waitForTransactionReceipt({ hash: txHash });
      addLog(`Audit transaction processed successfully on-chain! Status code: ${receipt.status || 'Success'}`, "success");

      addLog("Fetching Verifiable Security Certificate from contract storage...", "info");
      const cert = await client.readContract({
        address: contractAddress,
        functionName: "get_certificate",
        args: [codeHash]
      });

      // PythonTreeMap representation might return an empty dict/object if not found
      if (cert && cert.is_safe) {
        addLog("Certificate retrieved successfully! Contract code is verified SAFE.", "success");
        setCertificate(cert);
      } else {
        addLog("Audit transaction completed, but no safe certificate was registered. Code was rejected or marked unsafe by validators.", "error");
      }

    } catch (err) {
      addLog(`Execution error: ${err.message}`, "error");
      console.error(err);
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      {/* App Header */}
      <header className="app-header">
        <div className="brand">
          <Shield className="brand-icon" size={32} />
          <div>
            <h1>GenShield</h1>
            <div className="brand-tagline">On-Chain Intelligent Auditor</div>
          </div>
        </div>
        <div className="header-actions">
          <div className="network-badge">
            <span className="network-dot"></span>
            Studionet
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="main-grid">
        {/* Left column: Editor & controls */}
        <section className="glass-panel">
          <div className="panel-title">
            <FileCode size={20} color="var(--accent-cyan)" />
            <h2>Contract Auditor Panel</h2>
          </div>

          {/* Connection selection tabs */}
          <div className="form-group">
            <label className="form-label">Connection Type</label>
            <div className="tabs">
              <button 
                className={`tab-btn ${connectionType === 'wallet' ? 'active' : ''}`}
                onClick={() => setConnectionType('wallet')}
              >
                <Wallet size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Browser Wallet
              </button>
              <button 
                className={`tab-btn ${connectionType === 'key' ? 'active' : ''}`}
                onClick={() => setConnectionType('key')}
              >
                <Key size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Private Key
              </button>
            </div>
          </div>

          {/* Dynamic connection interface */}
          {connectionType === 'wallet' ? (
            <div className="form-group">
              <label className="form-label">EVM Wallet</label>
              {walletAddress ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', borderRadius: '12px', fontSize: '14px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                    {walletAddress.slice(0, 8)}...{walletAddress.slice(-8)}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle size={12} color="var(--accent-green)" /> Connected
                  </span>
                </div>
              ) : (
                <button className="btn-connect-wallet" onClick={connectWallet}>
                  <Wallet size={16} />
                  Connect Wallet (MetaMask/Rabby)
                </button>
              )}
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Private Key Hex</label>
              <div className="input-container">
                <Key className="input-icon" size={16} />
                <input 
                  type="password" 
                  placeholder="0x..." 
                  className="form-input" 
                  value={privateKey}
                  onChange={(e) => setPrivateKey(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Contract inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">GenShield Contract Address</label>
              <input 
                type="text" 
                className="form-input" 
                style={{ paddingLeft: '16px' }}
                value={contractAddress}
                onChange={(e) => setContractAddress(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Audit Contract Name</label>
              <input 
                type="text" 
                className="form-input" 
                style={{ paddingLeft: '16px' }}
                value={contractName}
                onChange={(e) => setContractName(e.target.value)}
              />
            </div>
          </div>

          {/* Custom Monaco-like editor */}
          <div className="form-group">
            <label className="form-label">Python Contract Source Code</label>
            <div className="code-editor-container">
              <div className="editor-header">
                <span className="editor-title">{contractName}.py</span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Python 3</span>
              </div>
              <div className="editor-body">
                <div className="editor-line-numbers">
                  {Array.from({ length: lineCount }).map((_, i) => (
                    <div key={i}>{i + 1}</div>
                  ))}
                </div>
                <textarea 
                  className="code-textarea"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  spellCheck="false"
                />
              </div>
            </div>
          </div>

          {/* Run button */}
          <button 
            className="btn-primary" 
            onClick={handleAudit} 
            disabled={isAuditing || (connectionType === 'key' && !privateKey)}
          >
            {isAuditing ? (
              <>
                <svg className="spinner" viewBox="0 0 50 50">
                  <circle className="path" cx="25" cy="25" r="20" fill="none" strokeWidth="5"></circle>
                </svg>
                Processing On-Chain Audit...
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                Run On-Chain Audit
              </>
            )}
          </button>
        </section>

        {/* Right column: Terminal log & Certificate badge */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Terminal Logs */}
          <div className="glass-panel" style={{ flex: 1 }}>
            <div className="panel-title">
              <Terminal size={20} color="var(--accent-purple)" />
              <h2>Consensus Console Log</h2>
            </div>
            
            <div className="terminal">
              <div className="terminal-header">
                <span className="terminal-dot red"></span>
                <span className="terminal-dot yellow"></span>
                <span className="terminal-dot green"></span>
                <span className="terminal-title">genshield-consensus-engine</span>
              </div>
              <div className="terminal-body">
                {logs.length === 0 && (
                  <div className="terminal-line sys">Consensus Console idle. Ready for auditing...</div>
                )}
                {logs.map((log, index) => (
                  <div key={index} className={`terminal-line ${log.type}`}>
                    <span style={{ color: 'rgba(255,255,255,0.2)', marginRight: '8px' }}>[{log.time}]</span>
                    {log.text}
                  </div>
                ))}
                <div ref={terminalEndRef} />
              </div>
            </div>
          </div>

          {/* Certificate Badge */}
          <div className="glass-panel" style={{ justifyContent: 'center' }}>
            <div className="panel-title">
              <Award size={20} color="var(--accent-green)" />
              <h2>Audit Certificate Registry</h2>
            </div>

            {certificate ? (
              <div className="certificate-card">
                <div className="certificate-header">
                  <div className="certificate-badge-icon">
                    <Shield size={24} />
                  </div>
                  <div className="certificate-title-box">
                    <h3>On-Chain Security Certificate</h3>
                    <p>VERIFIED SECURE BY CONSENSUS</p>
                  </div>
                </div>

                <div className="certificate-details">
                  <div className="detail-item">
                    <span className="detail-label">Contract Name</span>
                    <span className="detail-value">{certificate.contract_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Auditor Sender</span>
                    <span className="detail-value mono">
                      {certificate.auditor.slice(0, 6)}...{certificate.auditor.slice(-6)}
                    </span>
                  </div>
                  <div className="detail-item" style={{ gridColumn: 'span 2' }}>
                    <span className="detail-label">Source Hash (SHA-256)</span>
                    <span className="detail-value mono" style={{ fontSize: '10px' }}>
                      {certificate.code_hash}
                    </span>
                  </div>
                  <div className="detail-item" style={{ gridColumn: 'span 2' }}>
                    <span className="detail-label">Validation Date</span>
                    <span className="detail-value" style={{ fontSize: '11px' }}>
                      {new Date(certificate.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <div className="certificate-score">
                    <span className="score-label">Decentralized Security Rating</span>
                    <span className="score-value">{certificate.score}/100</span>
                  </div>
                </div>

                <a 
                  href={`https://studio.genlayer.com/contract/${contractAddress}`} 
                  target="_blank" 
                  rel="noreferrer"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12px', color: 'var(--accent-cyan)', textDecoration: 'none', marginTop: '4px' }}
                >
                  View Contract on GenLayer Explorer <ArrowUpRight size={12} />
                </a>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', border: '1px dashed var(--border-color)', borderRadius: '16px', color: 'var(--text-secondary)', textAlign: 'center', gap: '12px' }}>
                <Award size={48} style={{ opacity: 0.15 }} />
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: 'var(--text-primary)' }}>No Certificate Displayed</p>
                  <p style={{ fontSize: '12px', marginTop: '4px' }}>Run an audit. If the code passes validation, a verifiable security certificate card will render here.</p>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
