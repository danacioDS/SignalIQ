export const COMPANY_NAMES: Record<string, string> = {
  'AAPL': 'Apple Inc.',
  'MSFT': 'Microsoft Corp.',
  'NVDA': 'NVIDIA Corp.',
  'GOOGL': 'Alphabet Inc.',
  'META': 'Meta Platforms Inc.',
  'AMD': 'Advanced Micro Devices',
  'AMZN': 'Amazon.com Inc.',
  'TSLA': 'Tesla Inc.',
  'JPM': 'JPMorgan Chase & Co.',
  'KO': 'The Coca-Cola Company',
  'NOK': 'Nokia Oyj'
};

export const getCompanyName = (ticker: string): string => {
  return COMPANY_NAMES[ticker.toUpperCase()] || ticker;
};
