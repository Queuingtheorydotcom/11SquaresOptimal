#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
uint16_t reverse16(uint16_t x){uint16_t y=0;for(int i=0;i<16;i++)if(x&(1u<<i))y|=1u<<(15-i);return y;}
int main(int argc,char**argv){
 if(argc!=3)return 2;ifstream in(argv[1]);ofstream out(argv[2]);int ng,nm,np;in>>ng>>nm>>np;vector<uint16_t>pat(np),masks(nm);for(auto&p:pat){unsigned x;in>>x;p=x;}vector<array<uint16_t,16>>edge(ng);for(auto&a:edge)for(auto&v:a){unsigned x;in>>x;v=x;}for(auto&m:masks){unsigned x;in>>x;m=x;}
 vector<uint8_t>forbidden(65536,0);for(unsigned m=0;m<65536;m++)for(auto p:pat)if((m&p)==p)forbidden[m]=1;
 int initial=0;for(auto m:masks)initial+=forbidden[m];out<<"initial "<<initial<<"\n";int total=0;
 for(int round=1;;round++){
  int added=0;unsigned long long states=0;vector<string>passlines;
  for(int k=0;k<nm;k++){
   uint16_t source=masks[k];if(forbidden[source])continue;
   for(int gi=0;gi<ng;gi++){
    vector<int>order;for(int i=0;i<16;i++)if(source&(1u<<i))order.push_back(i);sort(order.begin(),order.end(),[&](int i,int j){return __builtin_popcount(edge[gi][i])<__builtin_popcount(edge[gi][j]);});
    vector<uint8_t>failed(65536,0);array<int,16>assignment;assignment.fill(-1);uint16_t survivor=0;
    auto dfs=[&](auto&&self,uint16_t used,int depth)->bool{
     states++;if(failed[used])return false;if(depth==11){if(!forbidden[used]){survivor=used;return true;}failed[used]=1;return false;}
     uint16_t options=edge[gi][order[depth]]&~used;while(options){int j=__builtin_ctz(options);options&=options-1;assignment[order[depth]]=j;if(self(self,used|(1u<<j),depth+1))return true;}failed[used]=1;return false;
    };
    if(!dfs(dfs,0,0)){forbidden[source]=forbidden[reverse16(source)]=1;added++;total++;out<<"excluded "<<round<<" "<<k<<" "<<gi<<"\n";break;}
    else{out<<"survivor "<<round<<" "<<k<<" "<<gi<<" "<<survivor;for(int i=0;i<16;i++)if(source&(1u<<i))out<<" "<<i<<":"<<assignment[i];out<<"\n";}
   }
  }
  out<<"round "<<round<<" added "<<added<<" states "<<states<<"\n";cerr<<"round "<<round<<" added "<<added<<" states "<<states<<"\n";if(!added)break;
 }
 out<<"new_excluded "<<total<<"\n";cerr<<"initial "<<initial<<" new "<<total<<"\n";
}
