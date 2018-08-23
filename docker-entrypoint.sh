#!/bin/sh

cd $(dirname $0)
case "$1" in
    server)
        export SYNCSERVER_SQLURI="${SYNCSERVER_SQLURI:-sqlite:///tmp/syncserver.db}"
        exec gunicorn \
            --bind ${HOST-0.0.0.0}:${PORT-5000}\
            --forwarded-allow-ips="${SYNCSERVER_FORWARDED_ALLOW_IPS:-127.0.0.1}"
            syncserver.wsgi_app
        ;;

    test_all)
        $0 test_flake8
        $0 test_nose
        $0 test_functional
        ;;

    test_flake8)
        echo "test - flake8"
        flake8 syncserver
        ;;

    test_nose)
        echo "test - nose"
        nosetests --verbose --nocapture syncstorage.tests
        ;;

    test_functional)
        echo "test - functional"
        # run functional tests
        gunicorn --paste ./syncserver/tests.ini &
        SERVER_PID=$!
        sleep 2

        $0 test_endpoint http://localhost:5000

        kill $SERVER_PID
        ;;

    test_endpoint)
        exec python -m syncstorage.tests.functional.test_storage \
            --use-token-server $2/token/1.0/sync/1.5
        ;;

    *)
        echo "Unknown CMD, $1"
        exit 1
        ;;
esac
