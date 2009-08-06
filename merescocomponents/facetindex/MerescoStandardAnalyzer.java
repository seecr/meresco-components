import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.LowerCaseFilter;
import org.apache.lucene.analysis.standard.StandardFilter;
import org.apache.lucene.analysis.standard.StandardTokenizer;


public class MerescoStandardAnalyzer extends Analyzer {
    public TokenStream tokenStream(String fieldName, java.io.Reader reader) {
        StandardTokenizer t = new StandardTokenizer(reader);
        StandardFilter f = new StandardFilter(t);
        LowerCaseFilter l = new LowerCaseFilter(f);
        return l;
    }
}
