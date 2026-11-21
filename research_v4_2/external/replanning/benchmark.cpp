#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <random>
#include <set>
#include <string>
#include <vector>
using namespace std;
using Clock=chrono::steady_clock;
constexpr int inf=1000000000;
struct Leg {int dep, from, arr, to, trip;};
struct Edge {int from,to,leg;};
struct Query {int origin,time,dest,start=-1;};
struct Route {int arrival=inf; vector<int> legs;};
struct Label {int time=inf,edge=-1;};
struct Saved {int v; Label label;};
struct Profile {vector<Label> labels; vector<unsigned char> queued;};

struct Network {
    int stations,trips;
    vector<Leg> legs;
    vector<Query> queries;
    vector<int> bans,targets;
    vector<pair<int,int>> vertices;
    vector<Edge> edges;
    vector<vector<int>> outgoing,incoming,cancel;
    vector<int> first;

    explicit Network(istream& in) {
        int n,q,b;
        in>>stations>>trips>>n>>q>>b;
        legs.resize(n);
        set<pair<int,int>> points;
        for(auto& l:legs) {
            in>>l.dep>>l.from>>l.arr>>l.to>>l.trip;
            points.emplace(l.dep,l.from); points.emplace(l.arr,l.to);
        }
        vertices.assign(points.begin(),points.end());
        map<pair<int,int>,int> ids;
        vector<vector<int>> local(stations);
        outgoing.resize(vertices.size()); incoming.resize(vertices.size()); cancel.resize(trips);
        for(int v=0;v<(int)vertices.size();v++) {
            ids[vertices[v]]=v;
            auto& chain=local[vertices[v].second];
            if(!chain.empty()) add(chain.back(),v,-1);
            chain.push_back(v);
        }
        for(int i=0;i<n;i++) {
            auto l=legs[i];
            int e=add(ids.at({l.dep,l.from}),ids.at({l.arr,l.to}),i);
            cancel[l.trip].push_back(e);
            first.push_back(l.dep);
        }
        for(int i=0;i<q;i++) {
            Query x; in>>x.origin>>x.time>>x.dest;
            auto& chain=local[x.origin];
            auto it=lower_bound(chain.begin(),chain.end(),x.time,[&](int v,int t){return vertices[v].first<t;});
            if(it!=chain.end()) x.start=*it;
            queries.push_back(x);
            if(find(targets.begin(),targets.end(),x.dest)==targets.end()) targets.push_back(x.dest);
        }
        bans.resize(b);
        for(int& h:bans) in>>h;
        if(!in || !is_sorted(first.begin(),first.end())) throw runtime_error("invalid network");
    }
    int add(int a,int b,int leg) {
        if(a>=b) throw runtime_error("backwards event");
        int k=edges.size();
        edges.push_back({a,b,leg}); outgoing[a].push_back(k); incoming[b].push_back(k);
        return k;
    }
    Label best(int v,int dest,int ban,const vector<Label>& labels) const {
        if(vertices[v].second==dest) return {vertices[v].first,-1};
        Label r;
        for(int e:outgoing[v]) {
            auto a=edges[e];
            if(a.leg>=0 && legs[a.leg].trip==ban) continue;
            if(labels[a.to].time<r.time) r={labels[a.to].time,e};
        }
        return r;
    }
    Profile solve(int dest,int ban) const {
        Profile p; p.labels.resize(vertices.size()); p.queued.resize(vertices.size());
        for(int v=(int)vertices.size()-1;v>=0;v--) p.labels[v]=best(v,dest,ban,p.labels);
        return p;
    }
    Route follow(const Query& x,const Profile& p) const {
        Route r;
        if(x.start<0) return r;
        r.arrival=p.labels[x.start].time;
        for(int v=x.start;p.labels[v].edge>=0;) {
            auto e=edges[p.labels[v].edge];
            if(e.leg>=0) r.legs.push_back(e.leg);
            v=e.to;
        }
        return r;
    }
    Route csa(const Query& x,int ban) const {
        vector<int> arrival(stations,inf), parent(stations,-1);
        arrival[x.origin]=x.time;
        for(int i=lower_bound(first.begin(),first.end(),x.time)-first.begin();i<(int)legs.size();i++) {
            auto l=legs[i];
            if(l.dep>=arrival[x.dest]) break;
            if(l.trip!=ban && arrival[l.from]<=l.dep && l.arr<arrival[l.to]) {
                arrival[l.to]=l.arr; parent[l.to]=i;
            }
        }
        Route r{arrival[x.dest],{}};
        for(int s=x.dest;parent[s]>=0;s=legs[parent[s]].from) r.legs.push_back(parent[s]);
        reverse(r.legs.begin(),r.legs.end());
        return r;
    }
    vector<Saved> update(Profile& p,int dest,int ban,bool selective) const {
        priority_queue<int> work;
        auto enqueue=[&](int v) {
            if(!p.queued[v]) {p.queued[v]=1;work.push(v);}
        };
        for(int e:cancel[ban]) {
            int v=edges[e].from;
            if(p.labels[v].edge==e) enqueue(v);
        }
        vector<Saved> changed;
        while(!work.empty()) {
            int v=work.top();work.pop();p.queued[v]=0;
            auto old=p.labels[v], updated=best(v,dest,ban,p.labels);
            if(old.edge==updated.edge && old.time==updated.time) continue;
            changed.push_back({v,old});p.labels[v]=updated;
            if(updated.time==old.time) continue;
            for(int e:incoming[v]) {
                int predecessor=edges[e].from;
                if(!selective || p.labels[predecessor].edge==e) enqueue(predecessor);
            }
        }
        return changed;
    }
};

enum Mode {SCAN, FULL, CACHED, ALL_PREDS, SELECTED};
const array<string,5> names={"csa","full_profile","path_cache","all_predecessors","candidate"};
struct Engine {
    const Network& g; Mode mode;
    map<int,Profile> profiles; vector<Route> cache;
    Engine(const Network& network,Mode m):g(network),mode(m) {
        if(m==CACHED) {
            for(auto x:g.queries) cache.push_back(g.csa(x,-1));
        }
        if(m==ALL_PREDS || m==SELECTED)
            for(int dest:g.targets) profiles.emplace(dest,g.solve(dest,-1));
    }
    vector<Route> run(int ban) {
        vector<Route> output; output.reserve(g.queries.size());
        if(mode==SCAN || mode==CACHED) {
            for(size_t i=0;i<g.queries.size();i++) {
                if(mode==CACHED && none_of(cache[i].legs.begin(),cache[i].legs.end(),[&](int l){return g.legs[l].trip==ban;}))
                    output.push_back(cache[i]);
                else output.push_back(g.csa(g.queries[i],ban));
            }
        } else {
            for(auto d:g.targets) {
                vector<Saved> backup;
                Profile temp;
                if(mode==FULL) temp=g.solve(d,ban);
                else backup=g.update(profiles.at(d),d,ban,mode==SELECTED);
                auto& p=mode==FULL?temp:profiles.at(d);
                for(auto x:g.queries) if(x.dest==d) output.push_back(g.follow(x,p));
                for(auto z:backup) p.labels[z.v]=z.label;
            }
        }
        return output;
    }
};
long long elapsed(Clock::time_point start) {
    return chrono::duration_cast<chrono::nanoseconds>(Clock::now()-start).count();
}
int main(int argc,char** argv) {
    if(argc!=5) return 2;
    ifstream src(argv[1]); Network graph(src);
    ofstream times(argv[2]), witnesses(argv[3]), startup(argv[4]);
    times<<"scenario,trip,repeat,method,ns\n";startup<<"method,ns\n";
    vector<Engine> engines; engines.reserve(5);
    for(auto m:{SCAN,FULL,CACHED,ALL_PREDS,SELECTED}) {
        auto start=Clock::now(); engines.emplace_back(graph,m);
        startup<<names[m]<<','<<elapsed(start)<<'\n';
    }
    mt19937 rng(4202); vector<int> order={0,1,2,3,4};
    for(size_t s=0;s<graph.bans.size();s++) for(int r=0;r<5;r++) {
        shuffle(order.begin(),order.end(),rng);
        for(int m:order) {
            auto start=Clock::now();
            auto routes=engines[m].run(graph.bans[s]);
            auto ns=elapsed(start);
            times<<s<<','<<graph.bans[s]<<','<<r<<','<<names[m]<<','<<ns<<'\n';
            if(r==0) {
                for(size_t q=0;q<routes.size();q++) {
                    witnesses<<s<<' '<<m<<' '<<q<<' '<<routes[q].arrival;
                    for(int leg:routes[q].legs) witnesses<<' '<<leg;
                    witnesses<<'\n';
                }
            }
        }
    }
}
