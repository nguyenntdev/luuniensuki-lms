// Single-thread native solvers. OR-Library files and warm witnesses are inputs only.
#include <algorithm>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include "core/cft.hpp"
#include "fixing/FixingData.hpp"

using Columns = std::vector<int>;
constexpr double budget = 5;
std::clock_t started;
int incumbent_cost;
const cft::FixingData* outer_fixing = nullptr;

double elapsed() { return double(std::clock() - started) / CLOCKS_PER_SEC; }

void record(int cost, const Columns& selected) {
    double stamp = elapsed();
    if (stamp > budget || cost >= incumbent_cost) return;
    incumbent_cost = cost;
    std::cout << std::setprecision(9) << stamp << ' ' << cost;
    for (int j : selected) std::cout << ' ' << j;
    std::cout << '\n';
}

// The build script installs observation calls on published incumbent updates.
void observe_cft(const cft::Solution& inner) {
    const auto& fixing = *outer_fixing;
    int cost = int(inner.cost + fixing.fixed_cost);
    if (cost >= incumbent_cost) return;
    Columns original = fixing.fixed_cols;
    for (auto j : inner.idxs) original.push_back(fixing.curr2orig.col_map[j]);
    record(cost, original);
}

#include "algorithms/Refinement.hpp"

struct Data {
    std::vector<int> costs;
    std::vector<Columns> rows, cols;
    explicit Data(const std::string& path) {
        std::ifstream in(path);
        int m,n;
        if (!(in >> m >> n)) throw std::runtime_error("matrix header");
        costs.resize(n); rows.resize(m); cols.resize(n);
        for (int& c : costs) in >> c;
        for (int i=0; i<m; ++i) {
            int count; in >> count;
            for (int k=0; k<count; ++k) {
                int j; in >> j;
                rows.at(i).push_back(j-1);
                cols.at(j-1).push_back(i);
            }
        }
        if (!in) throw std::runtime_error("truncated matrix");
    }
    int cost(const Columns& solution) const {
        int total=0;
        for (int j : solution) total += costs[j];
        return total;
    }
};

void search(const Data& data, const Columns& warm, int seed, bool single) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> unit(0.0,1.0);
    Columns current=warm, best=warm;
    int current_cost=data.cost(warm);
    std::vector<int> count(data.rows.size());
    Columns exposed;
    while (elapsed() < budget) {
        if (unit(rng) < 0.05) { current=best; current_cost=incumbent_cost; }
        Columns trial=current;
        std::shuffle(trial.begin(),trial.end(),rng);
        int upper=std::max(1,int(trial.size())/3);
        int drop=single ? 1 : std::uniform_int_distribution<int>(1,upper)(rng);
        trial.resize(trial.size()-drop);
        std::fill(count.begin(),count.end(),0);
        for (int j : trial) for (int i : data.cols[j]) ++count[i];
        exposed.clear();
        for (size_t i=0; i<count.size(); ++i) if (!count[i]) exposed.push_back(i);
        std::shuffle(exposed.begin(),exposed.end(),rng);
        for (int i : exposed) {
            if (count[i]) continue;
            int chosen=-1; double best_score=-1;
            for (int j : data.rows[i]) {
                int gain=0;
                for (int r : data.cols[j]) gain += count[r]==0;
                double score=(0.85+0.30*unit(rng))*gain/data.costs[j];
                if (score>best_score) { chosen=j; best_score=score; }
            }
            trial.push_back(chosen);
            for (int r : data.cols[chosen]) ++count[r];
        }
        // Test expensive columns first. Randomization before the stable sort resolves ties.
        std::shuffle(trial.begin(),trial.end(),rng);
        std::stable_sort(trial.begin(),trial.end(),[&](int a,int b){return data.costs[a]>data.costs[b];});
        Columns kept;
        for (int j : trial) {
            bool redundant=std::all_of(data.cols[j].begin(),data.cols[j].end(),[&](int i){return count[i]>1;});
            if (redundant) for (int r : data.cols[j]) --count[r];
            else kept.push_back(j);
        }
        int cost=data.cost(kept);
        if (cost<incumbent_cost && elapsed()<=budget) { best=kept; record(cost,kept); }
        double slack=double(current_cost)/current.size();
        if (cost<=current_cost || (cost<=current_cost+slack && unit(rng)<0.1)) {
            current=std::move(kept); current_cost=cost;
        }
    }
}

int main(int argc,char** argv) {
    if (argc!=5) return 2;
    Data data(argv[1]);
    std::ifstream supplied(argv[2]);
    Columns warm;
    for (int j; supplied>>j;) warm.push_back(j);
    if (warm.empty()) throw std::runtime_error("warm start");
    std::string method=argv[3];
    int seed=std::stoi(argv[4]);
    incumbent_cost=data.cost(warm);
    started=std::clock();
    if (method=="cft") {
        cft::Instance inst;
        inst.costs.assign(data.costs.begin(),data.costs.end());
        for (const auto& col : data.cols) {
            std::vector<cft::ridx_t> converted(col.begin(),col.end());
            inst.cols.push_back(converted);
        }
        inst.rows=data.rows;
        cft::Environment env;
        env.verbose=0;
        env.seed=seed;
        env.rnd=cft::prng_t(seed);
        // The callback scores process CPU. A generous wall guard allows the outer search to finish.
        env.time_limit=60;
        cft::Solution init{warm,float(incumbent_cost)};
        cft::run(env,inst,init);
    } else if (method=="adaptive" || method=="single") {
        search(data,warm,seed,method=="single");
    } else return 2;
    std::cout << "end " << std::setprecision(9) << elapsed() << '\n';
}
