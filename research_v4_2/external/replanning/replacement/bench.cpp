#include "corridor_engine.inc"

// Match indexed CSA's base witnesses and trip incidence exactly.
struct StationEngine : LazyEngine {
    vector<vector<int>> departures;
    StationEngine(const Network& g):LazyEngine(g,0),departures(g.stations) {
        for(int i=0;i<int(g.legs.size());++i) departures[g.legs[i].from].push_back(i);
    }
    Route repair(const Query& q,int ban) const {
        vector<int> time(graph.stations,inf), parent(graph.stations,-1);
        using Entry=pair<int,int>;
        priority_queue<Entry,vector<Entry>,greater<Entry>> queue;
        time[q.origin]=q.time;
        queue.emplace(q.time,q.origin);
        while(!queue.empty()) {
            auto [t,s]=queue.top();
            queue.pop();
            if(t!=time[s]) continue;
            if(s==q.dest) break;
            const auto& ids=departures[s];
            auto it=lower_bound(ids.begin(),ids.end(),t,[&](int i,int start){
                return graph.legs[i].dep<start;
            });
            for(;it!=ids.end();++it) {
                const auto& leg=graph.legs[*it];
                if(leg.dep>=time[q.dest]) break;
                if(leg.trip==ban || leg.arr>=time[leg.to]) continue;
                parent[leg.to]=*it;
                time[leg.to]=leg.arr;
                queue.emplace(leg.arr,leg.to);
            }
        }
        Route r{time[q.dest],{}};
        for(int s=q.dest;parent[s]>=0;s=graph.legs[parent[s]].from) r.legs.push_back(parent[s]);
        reverse(r.legs.begin(),r.legs.end());
        return r;
    }
    vector<Route> run(int ban) const {
        auto result=base;
        for(int i:affected[ban]) result[i]=repair(graph.queries[i],ban);
        return result;
    }
};
int main(int argc,char** argv) {
    if(argc!=5) return 2;
    ifstream in(argv[1]); Network g(in);
    ofstream timing(argv[2]), witness(argv[3]),setup(argv[4]);
    timing<<"scenario,trip,repeat,method,ns\n";setup<<"method,ns\n";
    vector<string> methods={"csa","full_profile","path_cache","all_predecessors","eager",
        "indexed_csa","lazy_unpruned","lazy_pruned","signature_only","corridor","candidate"};
    vector<unique_ptr<Engine>> orig;
    vector<unique_ptr<LazyEngine>> lazy;
    vector<unique_ptr<CorridorEngine>> follow;
    unique_ptr<StationEngine> station;
    vector<int> order;
    for(int i=0;i<int(methods.size());++i) {
        order.push_back(i);
        auto start=Clock::now();
        if(i<5) orig.push_back(make_unique<Engine>(g,static_cast<Mode>(i)));
        else if(i<8) lazy.push_back(make_unique<LazyEngine>(g,i-5));
        else if(i==10) station=make_unique<StationEngine>(g);
        else follow.push_back(make_unique<CorridorEngine>(g,i==9));
        setup<<methods[i]<<','<<elapsed(start)<<'\n';
    }
    mt19937 rng(4202);
    for(int s=0;s<int(g.bans.size());++s) for(int rep=0;rep<5;++rep) {
        shuffle(order.begin(),order.end(),rng);
        for(int i:order) {
            int ban=g.bans[s];
            auto start=Clock::now();
            auto routes=i<5?orig[i]->run(ban):i<8?lazy[i-5]->run(ban):i==10?station->run(ban):follow[i-8]->run(ban);
            auto ns=elapsed(start);
            timing<<s<<','<<ban<<','<<rep<<','<<methods[i]<<','<<ns<<'\n';
            if(rep==0) for(size_t q=0;q<routes.size();q++) {
                witness<<s<<' '<<i<<' '<<q<<' '<<routes[q].arrival;
                for(int leg:routes[q].legs) witness<<' '<<leg;
                witness<<'\n';
            }
        }
    }
}
