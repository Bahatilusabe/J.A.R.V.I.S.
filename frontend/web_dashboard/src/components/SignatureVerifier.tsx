import React, { useState, useCallback } from 'react';
import { Check, X, Clock, AlertCircle } from 'lucide-react';
import {
  DilithiumPublicKey,
  SignatureVerificationResult,
} from '../types/forensics.types';

// ============================================================================
// COMPONENT PROPS & INTERFACE
// ============================================================================

interface SignatureVerifierProps {
  signature: string;
  publicKey: DilithiumPublicKey;
  isVerifying?: boolean;
  verificationResult?: SignatureVerificationResult;
  onVerify: () => Promise<void>;
  reportId?: string;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const truncateKey = (key: string, visibleChars: number = 16): string => {
  if (key.length <= visibleChars * 2) return key;
  return `${key.substring(0, visibleChars)}...${key.substring(key.length - visibleChars)}`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const isKeyExpired = (expiresAt?: string): boolean => {
  if (!expiresAt) return false;
  return new Date(expiresAt) < new Date();
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const SignatureVerifier: React.FC<SignatureVerifierProps> = ({
  signature,
  publicKey,
  isVerifying = false,
  verificationResult,
  onVerify,
  // reportId, // Removed unused prop to fix lint warning
}) => {
  // =========================================================================
  // STATE
  // =========================================================================

  const [showFullSignature, setShowFullSignature] = useState(false);
  const [showFullKey, setShowFullKey] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [verifyError, setVerifyError] = useState<string>();

  const isExpired = isKeyExpired(publicKey.expiresAt);

  // =========================================================================
  // EVENT HANDLERS
  // =========================================================================

  const handleVerify = useCallback(async () => {
    try {
      setVerifyError(undefined);
      await onVerify();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Verification failed';
      setVerifyError(message);
    }
  }, [onVerify]);

  const handleCopySignature = useCallback(() => {
    navigator.clipboard.writeText(signature);
  }, [signature]);

  const handleCopyKey = useCallback(() => {
    navigator.clipboard.writeText(publicKey.publicKey);
  }, [publicKey]);

  // =========================================================================
  // RENDER - VERIFICATION STATUS BADGE
  // =========================================================================

  const renderStatusBadge = () => {
    if (isVerifying) {
      return (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            backgroundColor: '#fef3c7',
            border: '1px solid #fcd34d',
            borderRadius: '8px',
            color: '#92400e',
            fontSize: '13px',
            fontWeight: '600',
          }}
        >
          <Clock size={16} />
          Verifying...
        </div>
      );
    }

    if (verificationResult) {
      if (verificationResult.valid) {
        return (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: '#dcfce7',
              border: '1px solid #86efac',
              borderRadius: '8px',
              color: '#166534',
              fontSize: '13px',
              fontWeight: '600',
            }}
          >
            <Check size={16} />
            Signature Valid
          </div>
        );
      } else {
        return (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: '#fee2e2',
              border: '1px solid #fca5a5',
              borderRadius: '8px',
              color: '#991b1b',
              fontSize: '13px',
              fontWeight: '600',
            }}
          >
            <X size={16} />
            Signature Invalid
          </div>
        );
      }
    }

    return (
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          color: '#1e40af',
          fontSize: '13px',
          fontWeight: '600',
        }}
      >
        <AlertCircle size={16} />
        Not Verified
      </div>
    );
  };

  // =========================================================================
  // RENDER - KEY VALIDITY
  // =========================================================================

  const renderKeyValidity = () => {
    if (isExpired) {
      return (
        <div
          style={{
            padding: '8px 12px',
            backgroundColor: '#fee2e2',
            border: '1px solid #fca5a5',
            borderRadius: '6px',
            color: '#991b1b',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <X size={14} />
          Key Expired
        </div>
      );
    }

    if (publicKey.expiresAt) {
      const expiresDate = new Date(publicKey.expiresAt);
      const daysUntilExpiry = Math.ceil(
        (expiresDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      );

      if (daysUntilExpiry < 30) {
        return (
          <div
            style={{
              padding: '8px 12px',
              backgroundColor: '#fef3c7',
              border: '1px solid #fcd34d',
              borderRadius: '6px',
              color: '#92400e',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <AlertCircle size={14} />
            Expires in {daysUntilExpiry} days
          </div>
        );
      }

      return (
        <div
          style={{
            padding: '8px 12px',
            backgroundColor: '#dcfce7',
            border: '1px solid #86efac',
            borderRadius: '6px',
            color: '#166534',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Check size={14} />
          Valid until {formatDate(publicKey.expiresAt).split(' ')[0]}
        </div>
      );
    }

    return (
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: '#dcfce7',
          border: '1px solid #86efac',
          borderRadius: '6px',
          color: '#166534',
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <Check size={14} />
        Valid (No expiration)
      </div>
    );
  };

  // =========================================================================
  // RENDER
  // =========================================================================

  return (
    <div className="p-4 bg-gray-50 border border-gray-200 rounded flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="m-0 text-base font-bold text-gray-900">Dilithium Signature Verification</h3>
        {renderStatusBadge()}
      </div>

      {/* Divider */}
  <div className="h-px bg-gray-200" />

      {/* Public Key Section */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-gray-500">
          Public Key (Algorithm: {publicKey.algorithm})
        </label>
        <div
          className="px-3 py-2 bg-white border border-gray-300 rounded font-mono text-xs text-gray-700 break-all cursor-pointer transition-colors"
          onClick={() => setShowFullKey(!showFullKey)}
          title="Click to expand/collapse"
        >
          {showFullKey ? publicKey.publicKey : truncateKey(publicKey.publicKey)}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopyKey();
            }}
            className="float-right px-2 py-1 bg-gray-200 border-none rounded text-[10px] font-semibold text-gray-700 cursor-pointer"
            title="Copy to clipboard"
          >
            Copy
          </button>
        </div>
        <div className="flex gap-2 items-center">
          <div className="flex-1">{renderKeyValidity()}</div>
          <span className="text-[11px] text-gray-500">
            ID: {publicKey.keyId.substring(0, 8)}
          </span>
        </div>
      </div>

      {/* Signature Section */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-gray-500">Signature</label>
        <div
          className={`px-3 py-2 bg-white border border-gray-300 rounded font-mono text-xs text-gray-700 break-all cursor-pointer transition-colors ${showFullSignature ? '' : 'max-h-20 overflow-hidden'}`}
          onClick={() => setShowFullSignature(!showFullSignature)}
          title="Click to expand/collapse"
        >
          {showFullSignature ? signature : truncateKey(signature, 32)}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopySignature();
            }}
            className="float-right px-2 py-1 bg-gray-200 border-none rounded text-[10px] font-semibold text-gray-700 cursor-pointer"
            title="Copy to clipboard"
          >
            Copy
          </button>
        </div>
      </div>

      {/* Verification Result Details */}
      {verificationResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              padding: '8px 12px',
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '600',
              color: '#3b82f6',
              textAlign: 'left',
            }}
          >
            {isExpanded ? '▼ Hide Details' : '▶ Show Details'}
          </button>

          {isExpanded && (
            <div
              style={{
                padding: '12px',
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '12px',
                color: '#374151',
                display: 'grid',
                gridTemplateColumns: '140px 1fr',
                gap: '8px',
              }}
            >
              <span style={{ fontWeight: '600' }}>Verification Method:</span>
              <span>{verificationResult.verificationMethod}</span>

              <span style={{ fontWeight: '600' }}>Key ID:</span>
              <span style={{ fontFamily: 'monospace' }}>
                {verificationResult.keyId.substring(0, 16)}...
              </span>

              <span style={{ fontWeight: '600' }}>Algorithm:</span>
              <span>{verificationResult.algorithm}</span>

              <span style={{ fontWeight: '600' }}>Verified At:</span>
              <span>{formatDate(verificationResult.verifiedAt)}</span>

              <span style={{ fontWeight: '600' }}>Verification Time:</span>
              <span>{verificationResult.verificationTime}ms</span>

              {verificationResult.errorMessage && (
                <>
                  <span style={{ fontWeight: '600', color: '#dc2626' }}>Error:</span>
                  <span style={{ color: '#dc2626' }}>
                    {verificationResult.errorMessage}
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {verifyError && (
        <div
          style={{
            padding: '12px',
            backgroundColor: '#fee2e2',
            border: '1px solid #fca5a5',
            borderRadius: '6px',
            color: '#991b1b',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <X size={16} />
          {verifyError}
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleVerify}
        disabled={isVerifying || isExpired}
        style={{
          padding: '10px 16px',
          backgroundColor: isVerifying || isExpired ? '#d1d5db' : '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: isVerifying || isExpired ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: '600',
          transition: 'background-color 200ms',
          opacity: isVerifying || isExpired ? 0.7 : 1,
        }}
      >
        {isVerifying ? 'Verifying...' : 'Verify Signature'}
      </button>

      {/* Key Info */}
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #bfdbfe',
          borderRadius: '6px',
          fontSize: '11px',
          color: '#1e40af',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <div>
          <strong>Key Owner:</strong> {publicKey.keyOwner}
        </div>
        <div>
          <strong>Generated:</strong> {formatDate(publicKey.generatedAt)}
        </div>
        {publicKey.expiresAt && (
          <div>
            <strong>Expires:</strong> {formatDate(publicKey.expiresAt)}
          </div>
        )}
      </div>
    </div>
  );
};

export default SignatureVerifier;
