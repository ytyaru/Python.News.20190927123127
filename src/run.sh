RSS_LIST="`cat`"
[ -z "$RSS_LIST" ] && { echo -e "stdinにRSSのURLを指定してください。コード例は以下。\n" \
                "echo 'RSS1' | python3 get_news.py" \
                "echo -e 'RSS1\nRSS2\nRSS3' | python3 get_news.py ./news.db\n" \
                "cat rss_list_source1.txt   | python3 get_news.py ./news.db\n" \
                "第1引数にSQLite3DBファイル出力パスを指定できます。デフォルトは「./news.db」です。" 1>&2;
                exit 1; }
WORK_DIR="`pwd`"
SCRIPT_DIR="$(cd $(dirname $0); pwd)"
echo "$RSS_LIST" | python3 "$SCRIPT_DIR/get_news.py" "${1:-$WORK_DIR/news.db}"

