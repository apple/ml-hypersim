while true; do
    python download.py "$@"
    if [ $? -eq 0 ]; then
        break  # Exit loop if script succeeds
    fi
    echo "Download failed. Restarting in 10 seconds..."
    sleep 10
done

