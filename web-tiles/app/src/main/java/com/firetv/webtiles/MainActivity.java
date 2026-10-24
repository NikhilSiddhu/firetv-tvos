package com.firetv.webtiles;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * The tile grid. One entry per saved web shortcut, plus an "Add" tile at the end.
 *
 *   OK            open the site
 *   long-press OK edit
 *   Menu key      edit
 *   long-press... (Back) delete, asked first
 */
public class MainActivity extends Activity {

    private static final int REQ_EDIT = 1001;

    private final List<Tile> tiles = new ArrayList<>();
    private GridView grid;
    private TileAdapter adapter;
    private final ExecutorService pool = Executors.newFixedThreadPool(3);
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        grid = findViewById(R.id.grid);
        adapter = new TileAdapter();
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, position, id) -> onTileClicked(position));
        grid.setOnItemLongClickListener((parent, view, position, id) -> {
            onTileLongPressed(position);
            return true;
        });

        findViewById(R.id.hint).setOnClickListener(v ->
                Toast.makeText(this, R.string.hint_text, Toast.LENGTH_LONG).show());
    }

    @Override
    protected void onResume() {
        super.onResume();
        reload();
    }

    private void reload() {
        tiles.clear();
        tiles.addAll(TileStore.load(this));
        tiles.add(new Tile(getString(R.string.add_tile), "", ""));
        adapter.notifyDataSetChanged();
        warmIcons();
        focusFirstTile();
    }

    /** A TV remote needs something focused or the OK press goes nowhere. */
    private void focusFirstTile() {
        grid.post(() -> {
            if (grid.getChildCount() > 0) {
                grid.getChildAt(0).requestFocus();
            } else {
                grid.requestFocus();
            }
        });
    }

    /** Fetch any missing icons in the background, then refresh the grid. */
    private void warmIcons() {
        final List<Tile> snapshot = new ArrayList<>(tiles);
        pool.execute(() -> {
            boolean changed = false;
            for (Tile t : snapshot) {
                if (t.isAddPlaceholder()) continue;
                File f = IconLoader.iconFileFor(this, t);
                if (!f.exists()) {
                    if (IconLoader.fetch(this, t) != null) changed = true;
                }
            }
            if (changed) main.post(adapter::notifyDataSetChanged);
        });
    }

    private void onTileClicked(int position) {
        if (position < 0 || position >= tiles.size()) return;
        Tile t = tiles.get(position);
        if (t.isAddPlaceholder()) {
            startActivityForResult(new Intent(this, EditTileActivity.class), REQ_EDIT);
        } else {
            Intent i = new Intent(this, WebActivity.class);
            i.putExtra(WebActivity.EXTRA_URL, t.url);
            i.putExtra(WebActivity.EXTRA_NAME, t.name);
            startActivity(i);
        }
    }

    private void onTileLongPressed(int position) {
        if (position < 0 || position >= tiles.size()) return;
        Tile t = tiles.get(position);
        if (t.isAddPlaceholder()) {
            onTileClicked(position);
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle(t.name)
                .setItems(new CharSequence[]{"Edit", "Delete"}, (d, which) -> {
                    if (which == 0) {
                        Intent i = new Intent(this, EditTileActivity.class);
                        i.putExtra(EditTileActivity.EXTRA_INDEX, position);
                        i.putExtra(EditTileActivity.EXTRA_NAME, t.name);
                        i.putExtra(EditTileActivity.EXTRA_URL, t.url);
                        i.putExtra(EditTileActivity.EXTRA_ICON, t.iconUrl);
                        startActivityForResult(i, REQ_EDIT);
                    } else {
                        List<Tile> saved = TileStore.load(this);
                        int idx = indexOf(saved, t);
                        if (idx >= 0) {
                            saved.remove(idx);
                            TileStore.save(this, saved);
                            reload();
                        }
                    }
                })
                .show();
    }

    private int indexOf(List<Tile> list, Tile t) {
        for (int i = 0; i < list.size(); i++) {
            Tile o = list.get(i);
            if (o.url.equals(t.url) && o.name.equals(t.name)) return i;
        }
        return -1;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_EDIT && resultCode == RESULT_OK) reload();
    }

    @Override
    protected void onDestroy() {
        pool.shutdownNow();
        super.onDestroy();
    }

    // ---------------------------------------------------------------- adapter

    private class TileAdapter extends BaseAdapter {

        @Override
        public int getCount() {
            return tiles.size();
        }

        @Override
        public Object getItem(int position) {
            return tiles.get(position);
        }

        @Override
        public long getItemId(int position) {
            return position;
        }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView;
            if (v == null) v = getLayoutInflater().inflate(R.layout.item_tile, parent, false);

            ImageView icon = v.findViewById(R.id.icon);
            TextView label = v.findViewById(R.id.label);
            Tile t = tiles.get(position);

            if (t.isAddPlaceholder()) {
                icon.setImageResource(R.drawable.ic_add);
                label.setText(t.name);
            } else {
                label.setText(t.name);
                File f = IconLoader.iconFileFor(MainActivity.this, t);
                if (f.exists()) {
                    icon.setImageBitmap(BitmapFactory.decodeFile(f.getAbsolutePath()));
                } else {
                    icon.setImageResource(R.drawable.ic_globe);
                }
            }

            v.setOnFocusChangeListener((view, hasFocus) -> {
                view.animate().scaleX(hasFocus ? 1.08f : 1f)
                        .scaleY(hasFocus ? 1.08f : 1f).setDuration(120).start();
                view.setBackgroundResource(hasFocus ? R.drawable.tile_focus : R.drawable.tile_bg);
            });
            v.setBackgroundResource(v.hasFocus() ? R.drawable.tile_focus : R.drawable.tile_bg);

            // The tile view is focusable, so it receives the OK press itself rather than the
            // GridView. Handle it here.
            final int pos = position;
            v.setOnClickListener(view -> onTileClicked(pos));
            v.setOnLongClickListener(view -> {
                onTileLongPressed(pos);
                return true;
            });
            return v;
        }
    }
}
