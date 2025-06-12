import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  ExternalLink, 
  Clock, 
  CheckCircle, 
  XCircle, 
  TrendingUp, 
  Gift,
  Award
} from 'lucide-react';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await blockchainAPI.getTransactionHistory();
      setTransactions(response.transactions || []);
    } catch (error) {
      setError('Errore nel caricamento delle transazioni');
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'reward':
        return <Gift className="h-4 w-4 text-green-600" />;
      case 'achievement':
        return <Award className="h-4 w-4 text-yellow-600" />;
      case 'course_completion':
        return <TrendingUp className="h-4 w-4 text-blue-600" />;
      default:
        return <TrendingUp className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
      default:
        return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'pending':
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAddress = (address) => {
    if (!address) return 'N/A';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const openTransaction = (txHash) => {
    if (txHash) {
      // Ensure hash has 0x prefix for blockchain explorer
      const formattedHash = txHash.startsWith('0x') ? txHash : `0x${txHash}`;
      window.open(`https://amoy.polygonscan.com/tx/${formattedHash}`, '_blank');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cronologia Transazioni</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="ml-2 text-gray-600">Caricamento...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cronologia Transazioni</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={loadTransactions} variant="outline" size="sm">
              Riprova
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Cronologia Transazioni</CardTitle>
        <Button onClick={loadTransactions} variant="outline" size="sm">
          Aggiorna
        </Button>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Nessuna transazione trovata</p>
            <p className="text-sm text-gray-500 mt-2">
              Le tue transazioni TeoCoins appariranno qui
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getTransactionIcon(tx.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">
                          +{tx.amount} TEO
                        </span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${getStatusColor(tx.status)}`}
                        >
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(tx.status)}
                            <span className="capitalize">{tx.status}</span>
                          </div>
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-gray-600 mt-1">
                        {tx.description}
                      </p>
                      
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>{formatDate(tx.created_at)}</span>
                        {tx.to_address && (
                          <span>A: {formatAddress(tx.to_address)}</span>
                        )}
                        {tx.tx_hash && (
                          <span className="font-mono">
                            Hash: {tx.tx_hash.startsWith('0x') ? tx.tx_hash : `0x${tx.tx_hash}`}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {tx.tx_hash && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openTransaction(tx.tx_hash)}
                      className="flex-shrink-0"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TransactionHistory;