
from AlgorithmImports import *
import numpy as np

class RollContract(QCAlgorithm):

    def Initialize(self):
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        self.SetStartDate(2013, 1, 2)
        self.SetEndDate(2022,12,12)
        self.SetCash(1000000)
        res = Resolution.Minute 
        #CBOE only lists VIX Index at Daily level but can get vix options at minute level so get the options underlying price to get the minute VIX spot
        ticker =  'VIX'
        self.index_symbol = self.AddIndex(ticker, res).Symbol
        option = self.AddIndexOption(self.index_symbol, res)
        option.SetFilter(-1, 1, timedelta(0), timedelta(45))
        self.option_symbol = option.Symbol
        #add the front month UX futures, set to Raw
        # if we dont the beginning of the futures curve in history is going to be backwards stiched at astronoimical levels and will hide the true 
        # shape of the vol curve at that moment in time  
        self.ux_1 = self.AddFuture(Futures.Indices.VIX,
                                dataNormalizationMode=DataNormalizationMode.Raw,dataMappingMode = DataMappingMode.OpenInterest,contractDepthOffset = 0)
        
        #get etfs 
        self.spy = self.AddEquity("SPY",res).Symbol
        self.vixy = self.AddEquity("VIXY",res).Symbol
        self.svxy = self.AddEquity("SVXY",res).Symbol
        
        self.SetBenchmark("SPY")

        self.EnableAutomaticIndicatorWarmUp = True
        
  

    def OnData(self, slice):
        #create empty list for portfolio
        current_port_symbols = []
        
        # In case warming is required (for later use)
        if self.IsWarmingUp:
            return
        
        if slice.OptionChains.ContainsKey(self.option_symbol) and self.spy in slice.Bars and self.vixy in slice.Bars and self.svxy in slice.Bars:
            if self.Time.hour == 10 and self.Time.minute == 0:
                #get basis (vix fut/vix spot -1)
                vix_basis = (self.ux_1.Price/slice.OptionChains[self.option_symbol].Underlying.Price)-1
                #plot basis 
                self.Plot("VIX Basis", "Basis",vix_basis)
                
                #check current weight spy
                current_port_symbols = [ x.Symbol.Value for x in self.Portfolio.Values if x.Invested ]
                #current weight spy to later check to liquidate or not 
                

                self.Debug(f"current port symbols: {str(current_port_symbols)} DateTime: {self.Time}")
                if vix_basis > 0:
                    #if not long svxy and long vixy sell vixy buy svxy
                    if not "SVXY" in current_port_symbols:
                        if "VIXY" in current_port_symbols:
                            self.Liquidate("VIXY")
                            self.SetHoldings("SVXY",1)
                        else:
                            self.SetHoldings("SVXY",1)

                #if backwardated vol curve, 
                elif vix_basis < 0:
                    #if long vixy 
                    if not "VIXY" in current_port_symbols:
                        if "SVXY" in current_port_symbols:
                            self.Liquidate("SVXY")
                            self.SetHoldings("VIXY",1)
                        else:
                            self.SetHoldings("VIXY",1)
                            
                    
                    
                    

                
            
     
