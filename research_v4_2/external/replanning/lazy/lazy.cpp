// Reuse the immutable development graph, route type, and original five solver implementations.
#define main original_benchmark_main
#include "../benchmark.cpp"
#undef main
#include <cstdint>
#include <memory>

struct SuffixTable {
    Profile original;
    vector<uint64_t> trips;
    vector<Label> memo;
    vector<unsigned> epochs;
};

struct LazyEngine {
    const Network& graph;
    const int mode, words;
    vector<SuffixTable> tables;
    vector<int> destination;
    vector<vector<int>> affected;
    vector<Route> base;
    unsigned epoch = 0;

    LazyEngine(const Network& g, int variant)
        :graph(g),mode(variant),words((g.trips+63)/64),destination(g.stations,-1),affected(g.trips) {
        for(int dest:g.targets) {
            destination[dest]=tables.size();
            SuffixTable table;
            table.original=g.solve(dest,-1);
            if(mode!=0) {
                const int n=g.vertices.size();
                table.trips.assign(size_t(n)*words,0);
                table.memo.resize(n);
                table.epochs.assign(n,0);
                for(int v=n-1;v>=0;--v) {
                    const int e=table.original.labels[v].edge;
                    if(e<0) continue;
                    const Edge next=g.edges[e];
                    auto bits=table.trips.begin()+size_t(v)*words;
                    copy_n(table.trips.begin()+size_t(next.to)*words,words,bits);
                    if(next.leg>=0) {
                        const int trip=g.legs[next.leg].trip;
                        bits[trip/64]|=uint64_t(1)<<(trip%64);
                    }
                }
            }
            tables.push_back(move(table));
        }
        vector<int> seen(g.trips,-1);
        for(const Query& q:g.queries) {
            int i=base.size();
            base.push_back(g.follow(q,tables[destination[q.dest]].original));
            for(int leg:base.back().legs) {
                int t=g.legs[leg].trip;
                if(seen[t]!=i) affected[t].push_back(i);
                seen[t]=i;
            }
        }
    }
    Label search(SuffixTable& t,int v,int ban) {
        if(!(t.trips[size_t(v)*words+ban/64] & (uint64_t(1)<<(ban%64)))) return t.original.labels[v];
        if(t.epochs[v]==epoch) return t.memo[v];
        Label best;
        for(int edge:graph.outgoing[v]) {
            Edge next=graph.edges[edge];
            if(next.leg>=0 && graph.legs[next.leg].trip==ban) continue;
            if(mode==2 && t.original.labels[next.to].time>=best.time) continue;
            auto suffix=search(t,next.to,ban);
            if(suffix.time<best.time) best={suffix.time,edge};
        }
        t.epochs[v]=epoch;
        return t.memo[v]=best;
    }
    vector<Route> run(int ban) {
        ++epoch;
        vector<Route> output;
        output.reserve(base.size());
        auto it=affected[ban].begin();
        for(int i=0;i<(int)base.size();++i) {
            if(it==affected[ban].end() || *it!=i) { output.push_back(base[i]);continue; }
            ++it;
            const Query& q=graph.queries[i];
            if(mode==0) { output.push_back(graph.csa(q,ban));continue; }
            auto& t=tables[destination[q.dest]];
            int v=q.start;
            auto label=search(t,v,ban);
            Route r{label.time,{}};
            while(label.edge>=0) {
                auto edge=graph.edges[label.edge];
                if(edge.leg>=0) r.legs.push_back(edge.leg);
                v=edge.to;
                label=t.epochs[v]==epoch?t.memo[v]:t.original.labels[v];
            }
            output.push_back(move(r));
        }
        return output;
    }
};

int main(int argc,char** argv) {
    if(argc!=5) return 2;
    ifstream src(argv[1]); Network g(src);
    ofstream time(argv[2]), witnesses(argv[3]), startup(argv[4]);
    time<<"scenario,trip,repeat,method,ns\n";startup<<"method,ns\n";
    const vector<string> methods={"csa","full_profile","path_cache","all_predecessors","eager","indexed_csa","lazy_unpruned","candidate"};
    vector<unique_ptr<Engine>> old;
    vector<unique_ptr<LazyEngine>> study;
    for(int i=0;i<8;i++) {
        auto start=Clock::now();
        if(i<5) old.push_back(make_unique<Engine>(g,static_cast<Mode>(i)));
        else study.push_back(make_unique<LazyEngine>(g,i-5));
        startup<<methods[i]<<','<<elapsed(start)<<'\n';
    }
    mt19937 rng(4202);
    vector<int> order={0,1,2,3,4,5,6,7};
    for(int s=0;s<(int)g.bans.size();s++) for(int repeat=0;repeat<5;repeat++) {
        shuffle(order.begin(),order.end(),rng);
        for(int i:order) {
            auto start=Clock::now();
            auto result=i<5?old[i]->run(g.bans[s]):study[i-5]->run(g.bans[s]);
            auto ns=elapsed(start);
            time<<s<<','<<g.bans[s]<<','<<repeat<<','<<methods[i]<<','<<ns<<'\n';
            if(repeat==0) for(int q=0;q<(int)result.size();q++) {
                witnesses<<s<<' '<<i<<' '<<q<<' '<<result[q].arrival;
                for(int leg:result[q].legs) witnesses<<' '<<leg;
                witnesses<<'\n';
            }
        }
    }
}
