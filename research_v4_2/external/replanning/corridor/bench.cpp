// The build exposes unchanged historical solvers through lazy_engine.inc.
#include "lazy_engine.inc"

struct Corridor {
    Profile base;
    vector<uint64_t> signature, chain_signature;
    vector<int> end;
    vector<Label> memo;
    vector<unsigned> epochs;
};

struct CorridorEngine {
    const Network& g;
    bool contract;
    vector<Corridor> tables;
    vector<int> destination;
    vector<Route> base;
    vector<vector<int>> affected;
    unsigned epoch=0;

    static uint64_t bit(int t) {return uint64_t(1)<<(t%64);}

    CorridorEngine(const Network& graph,bool contraction)
        :g(graph),contract(contraction),destination(g.stations,-1),affected(g.trips) {
        for(int dest:g.targets) {
            destination[dest]=tables.size();
            Corridor c;
            c.base=g.solve(dest,-1);
            const int n=g.vertices.size();
            c.signature.resize(n);
            c.epochs.resize(n);
            c.memo.resize(n);
            if(contract) {c.chain_signature.resize(n);c.end.resize(n);}
            for(int v=n-1;v>=0;--v) {
                if(contract) c.end[v]=v;
                int edge=c.base.labels[v].edge;
                if(edge<0) continue;
                auto next=g.edges[edge];
                uint64_t used=next.leg<0?0:bit(g.legs[next.leg].trip);
                c.signature[v]=c.signature[next.to]|used;
                if(contract) {
                    int viable=count_if(g.outgoing[v].begin(),g.outgoing[v].end(),
                        [&](int e){return c.base.labels[g.edges[e].to].time<inf;});
                    if(viable==1) {
                        c.end[v]=c.end[next.to];
                        c.chain_signature[v]=c.chain_signature[next.to]|used;
                    }
                }
            }
            tables.push_back(move(c));
        }
        vector<int> last_query(g.trips,-1);
        for(auto& q:g.queries) {
            int i=base.size();
            base.push_back(g.follow(q,tables[destination[q.dest]].base));
            for(int l:base.back().legs) {
                int t=g.legs[l].trip;
                if(last_query[t]!=i) affected[t].push_back(i);
                last_query[t]=i;
            }
        }
    }

    Label solve(Corridor& c,int v,int ban) {
        if(!(c.signature[v]&bit(ban))) return c.base.labels[v];
        if(c.epochs[v]==epoch) return c.memo[v];
        Label best;
        if(contract && c.end[v]!=v) {
            bool broken=false;
            if(c.chain_signature[v]&bit(ban)) {
                for(int p=v;p!=c.end[v];) {
                    const auto e=g.edges[c.base.labels[p].edge];
                    if(e.leg>=0 && g.legs[e.leg].trip==ban) {broken=true;break;}
                    p=e.to;
                }
            }
            if(!broken) {
                auto tail=solve(c,c.end[v],ban);
                if(tail.time<inf) best={tail.time,c.base.labels[v].edge};
            }
        } else {
            for(int e:g.outgoing[v]) {
                const auto next=g.edges[e];
                if(next.leg>=0 && g.legs[next.leg].trip==ban) continue;
                if(c.base.labels[next.to].time>=best.time) continue;
                auto tail=solve(c,next.to,ban);
                if(tail.time<best.time) best={tail.time,e};
            }
        }
        c.epochs[v]=epoch;
        return c.memo[v]=best;
    }

    vector<Route> run(int ban) {
        ++epoch;
        vector<Route> output;
        output.reserve(base.size());
        auto invalid=affected[ban].begin();
        for(size_t i=0;i<base.size();++i) {
            if(invalid==affected[ban].end() || *invalid!=int(i)) {
                output.push_back(base[i]);continue;
            }
            ++invalid;
            const auto& q=g.queries[i];
            auto& c=tables[destination[q.dest]];
            int v=q.start;
            auto label=solve(c,v,ban);
            Route r{label.time,{}};
            while(label.edge>=0) {
                auto e=g.edges[label.edge];
                if(e.leg>=0) r.legs.push_back(e.leg);
                v=e.to;
                label=c.epochs[v]==epoch?c.memo[v]:c.base.labels[v];
            }
            output.push_back(move(r));
        }
        return output;
    }
};

int main(int argc,char** argv) {
    if(argc!=5) return 2;
    ifstream in(argv[1]); Network g(in);
    ofstream timing(argv[2]), witness(argv[3]),setup(argv[4]);
    timing<<"scenario,trip,repeat,method,ns\n";setup<<"method,ns\n";
    vector<string> methods={"csa","full_profile","path_cache","all_predecessors","eager",
        "indexed_csa","lazy_unpruned","lazy_pruned","signature_only","candidate"};
    vector<unique_ptr<Engine>> orig;
    vector<unique_ptr<LazyEngine>> lazy;
    vector<unique_ptr<CorridorEngine>> follow;
    vector<int> order;
    for(int i=0;i<int(methods.size());++i) {
        order.push_back(i);
        auto start=Clock::now();
        if(i<5) orig.push_back(make_unique<Engine>(g,static_cast<Mode>(i)));
        else if(i<8) lazy.push_back(make_unique<LazyEngine>(g,i-5));
        else follow.push_back(make_unique<CorridorEngine>(g,i==9));
        setup<<methods[i]<<','<<elapsed(start)<<'\n';
    }
    mt19937 rng(4202);
    for(int s=0;s<int(g.bans.size());++s) for(int rep=0;rep<5;++rep) {
        shuffle(order.begin(),order.end(),rng);
        for(int i:order) {
            int ban=g.bans[s];
            auto start=Clock::now();
            auto routes=i<5?orig[i]->run(ban):i<8?lazy[i-5]->run(ban):follow[i-8]->run(ban);
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
