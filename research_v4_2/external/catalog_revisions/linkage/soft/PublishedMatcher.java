import com.wcohen.ss.BasicStringWrapper;
import com.wcohen.ss.BasicStringWrapperIterator;
import com.wcohen.ss.SoftTFIDF;
import com.wcohen.ss.api.StringWrapper;
import java.nio.file.*;
import java.io.*;
import java.util.*;

public class PublishedMatcher {
    public static void main(String[] args) throws IOException {
        List<String> rows = Files.readAllLines(Path.of(args[0]));
        Set<String> docs = new TreeSet<>();
        for (String row : rows) {
            String[] columns = row.split("\\t", -1);
            if (columns[0].equals("fit")) {
                docs.add(columns[1]);
                docs.add(columns[2]);
            }
        }
        SoftTFIDF distance = new SoftTFIDF();
        List<StringWrapper> corpus = new ArrayList<>();
        for (String doc : docs) corpus.add(new BasicStringWrapper(doc));
        distance.train(new BasicStringWrapperIterator(corpus.iterator()));
        Map<String, StringWrapper> prepared = new HashMap<>();
        try (BufferedWriter out = Files.newBufferedWriter(Path.of(args[1]))) {
            for (String row : rows) {
                String[] columns = row.split("\\t", -1);
                StringWrapper left = prepared.computeIfAbsent(columns[1], distance::prepare);
                StringWrapper right = prepared.computeIfAbsent(columns[2], distance::prepare);
                out.write(Double.toString(distance.score(left, right)));
                out.newLine();
            }
        }
    }
}
