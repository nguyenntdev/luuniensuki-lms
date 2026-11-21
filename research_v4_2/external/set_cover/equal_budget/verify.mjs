// Independent row-wise replay, using only Node's standard library.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';

const [source, recorded, report] = process.argv.slice(2);
if (!report) throw new Error('verify.mjs matrix_directory run_directory summary.json');
const families = ['e','f','g','h'];
const methods = ['greedy','exchange','single','cft','zhu','highs'];
const candidates = ['adaptive', ...methods];
const effects = Object.fromEntries(methods.map(m => [m, []]));
const costs = [];
let checked = 0;
const mean = x => x.reduce((a,b) => a+b,0)/x.length;
const ascending = (a,b) => a-b;
const median = x => [...x].sort(ascending)[Math.floor(x.length/2)];

for (const family of families) {
    for (let i=1; i<=5; ++i) {
        const name = 'scpnr'+family+i;
        const raw = readFileSync(join(source,name+'.txt'));
        const result = JSON.parse(readFileSync(join(recorded,name+'.json'),'utf8'));
        assert.equal(result.instance,name);
        assert.equal(result.sha256,createHash('sha256').update(raw).digest('hex'));
        assert.deepEqual(Object.keys(result.runs).sort(),[...candidates].sort());
        assert.equal(result.budget_cpu_s,5);
        const tokens = raw.toString().trim().split(/\s+/).map(Number);
        let k=0;
        const m=tokens[k++], n=tokens[k++];
        assert.equal(result.rows,m);
        assert.equal(result.columns,n);
        const weights=tokens.slice(k,k+n);
        k+=n;
        const rows=[];
        for (let r=0; r<m; ++r) {
            const length=tokens[k++];
            const row=tokens.slice(k,k+length);
            assert(row.every(j => Number.isInteger(j) && j>=1 && j<=n));
            assert.equal(new Set(row).size,length);
            rows.push(row);
            k+=length;
        }
        assert.equal(k,tokens.length);
        assert.equal(result.incidences,rows.reduce((a,row) => a+row.length,0));
        const medians={};
        for (const method of candidates) {
            const runs = result.runs[method];
            assert.deepEqual(runs.map(r => r.seed), ['greedy','exchange'].includes(method) ? [0] : [11,29,47]);
            for (const run of runs) {
                const cols = new Set(run.columns_one_based);
                assert.equal(cols.size,run.columns_one_based.length);
                assert([...cols].every(j => Number.isInteger(j) && j>=1 && j<=n));
                assert(rows.every(row => row.some(j => cols.has(j))), name+' '+method+' misses a row');
                assert.equal([...cols].reduce((s,j) => s+weights[j-1],0),run.cost);
                assert(run.first_best_cpu_s>=0 && run.first_best_cpu_s<=result.budget_cpu_s);
                assert(run.first_best_cpu_s<=run.observed_cpu_s+0.000001);
                ++checked;
            }
            medians[method]=median(runs.map(r => r.cost));
        }
        costs.push({name,medians});
        for (const method of methods)
            effects[method].push((medians[method]-medians.adaptive)/medians[method]);
    }
}

function signFlip(e) {
    const scores=e.filter(x => x!==0);
    const observed=scores.reduce((a,b) => a+b,0);
    let above=0;
    function enumerate(i,sum) {
        if (i===scores.length) {
            if (sum>=observed-1e-12) ++above;
        } else {
            enumerate(i+1,sum+scores[i]);
            enumerate(i+1,sum-scores[i]);
        }
    }
    enumerate(0,0);
    return above/2**scores.length;
}

function bootstrap(e) {
    let state=162;
    function next() {
        state=(Math.imul(1664525,state)+1013904223)>>>0;
        return state/4294967296;
    }
    const sample=[];
    for (let b=0; b<20000; ++b) {
        let sum=0;
        for (let family=0; family<4; ++family)
            for (let draw=0; draw<5; ++draw)
                sum+=e[family*5+Math.floor(next()*5)];
        sample.push(sum/20);
    }
    sample.sort(ascending);
    function quantile(q) {
        const index=(sample.length-1)*q, left=Math.floor(index), weight=index-left;
        return sample[left]*(1-weight)+sample[left+1]*weight;
    }
    return [quantile(0.025),quantile(0.975)];
}

const comparisons=methods.map(baseline => {
    const d=effects[baseline];
    return {baseline,mean_saving:mean(d),interval:bootstrap(d),raw_p:signFlip(d),
        wins:d.filter(x => x>0).length,ties:d.filter(x => x===0).length,losses:d.filter(x => x<0).length,
        by_family:Object.fromEntries(families.map((f,i) => [f,mean(d.slice(5*i,5*i+5))]))};
});
const ranked=[...comparisons].sort((a,b) => a.raw_p-b.raw_p);
let previous=0;
for (const [i,r] of ranked.entries()) {
    previous=Math.min(1,Math.max(previous,r.raw_p*(ranked.length-i)));
    r.holm_p=previous;
    r.pass=r.mean_saving>=0.01 && r.interval[0]>0 && r.holm_p<0.05;
}
const summary={instances:costs.length,witnesses_checked:checked,bootstrap_samples:20000,
    comparisons,all_pass:comparisons.every(r => r.pass),costs};
writeFileSync(report,JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({instances:costs.length,witnesses:checked,all_pass:summary.all_pass}));
