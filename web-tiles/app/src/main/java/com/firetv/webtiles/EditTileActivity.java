package com.firetv.webtiles;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * The "add to home screen" form: a name, a web address, and an optional icon address.
 * If no icon address is given the site's own favicon is fetched automatically.
 */
public class EditTileActivity extends Activity {

    public static final String EXTRA_INDEX = "index";
    public static final String EXTRA_NAME = "name";
    public static final String EXTRA_URL = "url";
    public static final String EXTRA_ICON = "icon";

    private EditText nameField, urlField, iconField;
    private TextView status;
    private Button save;
    private int editIndex = -1;

    private final ExecutorService pool = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_edit);

        nameField = findViewById(R.id.field_name);
        urlField = findViewById(R.id.field_url);
        iconField = findViewById(R.id.field_icon);
        status = findViewById(R.id.status);
        save = findViewById(R.id.save);
        Button cancel = findViewById(R.id.cancel);

        editIndex = getIntent().getIntExtra(EXTRA_INDEX, -1);
        if (editIndex >= 0) {
            nameField.setText(getIntent().getStringExtra(EXTRA_NAME));
            urlField.setText(getIntent().getStringExtra(EXTRA_URL));
            iconField.setText(getIntent().getStringExtra(EXTRA_ICON));
            ((TextView) findViewById(R.id.title)).setText(R.string.edit_tile);
        }

        save.setOnClickListener(v -> onSave());
        cancel.setOnClickListener(v -> finish());
    }

    private void onSave() {
        final String name = nameField.getText().toString().trim();
        final String rawUrl = urlField.getText().toString().trim();
        final String iconUrl = iconField.getText().toString().trim();

        if (TextUtils.isEmpty(name)) {
            Toast.makeText(this, R.string.need_name, Toast.LENGTH_SHORT).show();
            return;
        }
        if (TextUtils.isEmpty(rawUrl)) {
            Toast.makeText(this, R.string.need_url, Toast.LENGTH_SHORT).show();
            return;
        }

        final String url = TileStore.normaliseUrl(rawUrl);
        save.setEnabled(false);
        status.setText(getString(R.string.fetching_icon));

        pool.execute(() -> {
            Tile probe = new Tile(name, url, iconUrl);
            boolean ok = IconLoader.fetch(EditTileActivity.this, probe) != null;

            main.post(() -> {
                List<Tile> tiles = TileStore.load(EditTileActivity.this);
                if (editIndex >= 0 && editIndex < tiles.size()) {
                    tiles.set(editIndex, probe);
                } else {
                    tiles.add(probe);
                }
                TileStore.save(EditTileActivity.this, tiles);
                Toast.makeText(EditTileActivity.this,
                        ok ? R.string.saved_with_icon : R.string.saved_no_icon,
                        Toast.LENGTH_SHORT).show();
                setResult(RESULT_OK);
                finish();
            });
        });
    }

    @Override
    protected void onDestroy() {
        pool.shutdownNow();
        super.onDestroy();
    }
}
