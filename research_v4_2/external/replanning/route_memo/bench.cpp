#include "corridor_engine.inc"

constexpr int repeats = 15;
constexpr int setup_repeats = 7;

struct RideIndex {
    vector<int> base_head;
    vector<int> repaired_head;
    vector<unsigned> epochs;
};

template<bool memoize>
struct RideEngine : CorridorEngine {
    vector<RideIndex> rides;

    explicit RideEngine(const Network& graph) : CorridorEngine(graph, false) {
        const int count = graph.vertices.size();
        for (const auto& table : tables) {
            RideIndex index;
            index.base_head.resize(count, -1);
            if constexpr (memoize) {
                index.repaired_head.resize(count);
                index.epochs.resize(count);
            }
            for (int v = count - 1; v >= 0; --v) {
                const int e = table.base.labels[v].edge;
                if (e < 0) continue;
                const auto edge = graph.edges[e];
                index.base_head[v] = edge.leg < 0 ? index.base_head[edge.to] : e;
            }
            rides.push_back(move(index));
        }
    }

    int first_ride(const Corridor& table, RideIndex& index, int v) const {
        if (table.epochs[v] != epoch) return index.base_head[v];
        if (index.epochs[v] == epoch) return index.repaired_head[v];

        int edge = table.memo[v].edge;
        if (edge >= 0 && g.edges[edge].leg < 0) {
            edge = first_ride(table, index, g.edges[edge].to);
        }
        index.repaired_head[v] = edge;
        index.epochs[v] = epoch;
        return edge;
    }

    Route repair(int query_id, int ban) {
        const auto& query = g.queries[query_id];
        const int dest = destination[query.dest];
        auto& table = tables[dest];
        auto& index = rides[dest];
        auto label = solve(table, query.start, ban);
        Route route{label.time, {}};
        if (label.time == inf) return route;
        route.legs.reserve(base[query_id].legs.size());

        int v = query.start;
        if constexpr (memoize) {
            for (int e = first_ride(table, index, v); e >= 0;) {
                const auto edge = g.edges[e];
                route.legs.push_back(edge.leg);
                e = first_ride(table, index, edge.to);
            }
        } else {
            // Traverse the repaired prefix, then use the same base ride index.
            while (table.epochs[v] == epoch) {
                const int e = table.memo[v].edge;
                if (e < 0) return route;
                const auto edge = g.edges[e];
                if (edge.leg >= 0) route.legs.push_back(edge.leg);
                v = edge.to;
            }
            for (int e = index.base_head[v]; e >= 0; e = index.base_head[g.edges[e].to]) {
                route.legs.push_back(g.edges[e].leg);
            }
        }
        return route;
    }

    vector<Route> run(int ban) {
        ++epoch;
        vector<Route> output;
        output.reserve(base.size());
        auto invalid = affected[ban].begin();
        for (int i = 0; i < int(base.size()); ++i) {
            if (invalid != affected[ban].end() && *invalid == i) {
                output.push_back(repair(i, ban));
                ++invalid;
            } else {
                output.push_back(base[i]);
            }
        }
        return output;
    }
};

const array<string, 4> methods = {
    "indexed_csa", "signature_only", "signature_base_index", "memoized_rides"
};

struct Solver {
    virtual vector<Route> run(int ban) = 0;
    virtual ~Solver() = default;
};

template<class EngineType>
struct BenchmarkSolver : Solver {
    EngineType engine;

    template<class... Args>
    explicit BenchmarkSolver(Args&&... args) : engine(forward<Args>(args)...) {}

    vector<Route> run(int ban) override { return engine.run(ban); }
};

unique_ptr<Solver> construct(const Network& g, int method) {
    switch (method) {
        case 0: return make_unique<BenchmarkSolver<LazyEngine>>(g, 0);
        case 1: return make_unique<BenchmarkSolver<CorridorEngine>>(g, false);
        case 2: return make_unique<BenchmarkSolver<RideEngine<false>>>(g);
        case 3: return make_unique<BenchmarkSolver<RideEngine<true>>>(g);
    }
    throw logic_error("unknown method");
}

void check_repeat(const vector<Route>& expected, const vector<Route>& actual) {
    if (expected.size() != actual.size()) throw logic_error("incomplete batch");
    for (size_t i = 0; i < actual.size(); ++i) {
        if (expected[i].arrival != actual[i].arrival || expected[i].legs != actual[i].legs) {
            throw logic_error("witness changed across repetitions");
        }
    }
}

int main(int argc, char** argv) {
    if (argc != 5) return 2;
    ifstream input(argv[1]);
    Network g(input);
    ofstream timing(argv[2]), witness(argv[3]), setup(argv[4]);
    timing << "scenario,trip,repeat,method,ns\n";
    setup << "repeat,method,ns\n";
    mt19937 rng(4202);
    array<int, methods.size()> order{0, 1, 2, 3};
    array<unique_ptr<Solver>, methods.size()> solvers;
    for (int rep = 0; rep < setup_repeats; ++rep) {
        shuffle(order.begin(), order.end(), rng);
        for (int m : order) {
            auto start = Clock::now();
            auto solver = construct(g, m);
            auto ns = elapsed(start);
            setup << rep << ',' << methods[m] << ',' << ns << '\n';
            if (rep == setup_repeats - 1) solvers[m] = move(solver);
        }
    }

    for (int s = 0; s < int(g.bans.size()); ++s) {
        int ban = g.bans[s];
        array<vector<Route>, methods.size()> expected;
        shuffle(order.begin(), order.end(), rng);
        for (int m : order) expected[m] = solvers[m]->run(ban);
        for (int rep = 0; rep < repeats; ++rep) {
            shuffle(order.begin(), order.end(), rng);
            for (int m : order) {
                auto start = Clock::now();
                auto routes = solvers[m]->run(ban);
                auto ns = elapsed(start);
                timing << s << ',' << ban << ',' << rep << ',' << methods[m] << ',' << ns << '\n';
                check_repeat(expected[m], routes);
            }
        }
        for (int m : order) {
            for (size_t q = 0; q < expected[m].size(); ++q) {
                const auto& route = expected[m][q];
                witness << s << ' ' << m << ' ' << q << ' ' << route.arrival;
                for (int leg : route.legs) witness << ' ' << leg;
                witness << '\n';
            }
        }
    }
    return timing && witness && setup ? 0 : 1;
}
