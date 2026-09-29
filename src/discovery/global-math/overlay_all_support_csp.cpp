#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int main(int argc,char**argv){
 if(argc<3)return 2;ifstream in(argv[1]);ofstream out(argv[2]);int nr,np,nm,npat;in>>nr>>np>>nm>>npat;vector<uint16_t>patterns(npat);for(auto&p:patterns){unsigned x;in>>x;p=x;}vector<array<int,4>>labels(nr);array<vector<int>,16>domains;for(int r=0;r<nr;r++){for(auto&x:labels[r])in>>x;domains[labels[r][0]].push_back(r);}vector<vector<uint8_t>>ban(nr,vector<uint8_t>(nr));for(int k=0;k<np;k++){int i,j;in>>i>>j;ban[i][j]=ban[j][i]=1;}vector<uint16_t>masks(nm);for(auto&m:masks){unsigned x;in>>x;m=x;}long long limit=argc>3?stoll(argv[3]):100000;int start=argc>4?stoi(argv[4]):0,end=argc>5?stoi(argv[5]):nm;int pass=0,unk=0,infeas=0,skip=0;long long allnodes=0;
 array<uint8_t,65536> supported{};
 for(unsigned m=0;m<65536;m++)if(__builtin_popcount(m)==11){bool bad=false;for(auto p:patterns)if((m&p)==p){bad=true;break;}if(!bad){unsigned k=m;while(true){supported[k]=1;if(!k)break;k=(k-1)&m;}}}
 auto forbidden=[&](uint16_t mask){return !supported[mask];};
 for(int mi=start;mi<end;mi++){
  if(forbidden(masks[mi])){skip++;continue;}for(int forced=0;forced<nr;forced++){if(!(masks[mi]&(1u<<labels[forced][0])))continue;array<uint16_t,4>used{};vector<int>chosen;long long nodes=0;bool timeout=false;vector<int>solution;
  auto legal=[&](int r){if(labels[r][0]==labels[forced][0] && r!=forced)return false;for(int g=0;g<4;g++){uint16_t b=1u<<labels[r][g];if(used[g]&b)return false;if(forbidden(used[g]|b))return false;}for(int s:chosen)if(ban[r][s])return false;return true;};
  auto dfs=[&](auto&&self,uint16_t remain)->bool{
   if(++nodes>limit){timeout=true;return false;}if(!remain){solution=chosen;return true;}
   int selected=-1;vector<int>best;
   for(int i=0;i<16;i++)if(remain&(1u<<i)){
    vector<int>possible;for(int r:domains[i])if(legal(r))possible.push_back(r);if(possible.empty())return false;if(selected==-1||possible.size()<best.size()){selected=i;best=possible;if(best.size()==1)break;}
   }
   for(int r:best){for(int g=0;g<4;g++)used[g]|=1u<<labels[r][g];chosen.push_back(r);if(self(self,remain&~(1u<<selected)))return true;chosen.pop_back();for(int g=0;g<4;g++)used[g]&=~(1u<<labels[r][g]);if(timeout)return false;}
   return false;
  };
  bool found=dfs(dfs,masks[mi]);allnodes+=nodes;if(found){pass++;out<<"SURVIVES "<<mi<<" "<<forced<<" "<<nodes;for(int r:solution)out<<" "<<r;out<<"\n";}else if(timeout){unk++;out<<"UNKNOWN "<<mi<<" "<<forced<<" "<<nodes<<"\n";}else{infeas++;out<<"EXCLUDED "<<mi<<" "<<forced<<" "<<nodes<<"\n";}out.flush();
  }if(mi%100==0)cerr<<"progress "<<mi<<" excluded "<<infeas<<" survive "<<pass<<" unknown "<<unk<<"\n";
 }
 out<<"SUMMARY excluded "<<infeas<<" survive "<<pass<<" unknown "<<unk<<" skip "<<skip<<" nodes "<<allnodes<<"\n";cerr<<"SUMMARY excluded "<<infeas<<" survive "<<pass<<" unknown "<<unk<<" skip "<<skip<<" nodes "<<allnodes<<"\n";
}
