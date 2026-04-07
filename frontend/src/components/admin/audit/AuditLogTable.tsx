'use client';

import { useEffect, useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { AuditLogRecord, adminAPI } from '@/lib/api/admin';

import { SessionReviewDialog } from './SessionReviewDialog';

const PAGE_SIZE = 10;

export function AuditLogTable() {
  const [rows, setRows] = useState<AuditLogRecord[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedAudit, setSelectedAudit] = useState<AuditLogRecord | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadRows();
    }, 250);
    return () => clearTimeout(timer);
  }, [page, search]);

  const loadRows = async () => {
    setLoading(true);
    try {
      const data = await adminAPI.getAuditLogs({
        page,
        page_size: PAGE_SIZE,
        q: search || undefined,
      });
      setRows(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load audit logs', err);
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  const openSessionReview = (row: AuditLogRecord) => {
    setSelectedAudit(row);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center gap-3 flex-wrap">
          <Input
            value={search}
            onChange={(e) => {
              setPage(1);
              setSearch(e.target.value);
            }}
            placeholder="Search input/output/model/session..."
            className="max-w-md"
          />
          <Button variant="outline" onClick={() => void loadRows()} disabled={loading}>
            Refresh
          </Button>
          <p className="text-sm text-muted-foreground ml-auto">
            Showing page {page} of {totalPages} ({total} logs)
          </p>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-semibold">Timestamp</th>
                <th className="text-left p-3 font-semibold">Decision</th>
                <th className="text-left p-3 font-semibold">Input</th>
                <th className="text-left p-3 font-semibold">Output</th>
                <th className="text-left p-3 font-semibold">Confidence</th>
                <th className="text-left p-3 font-semibold">Model</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td className="p-4 text-muted-foreground" colSpan={6}>
                    Loading audit logs...
                  </td>
                </tr>
              )}
              {!loading && rows.length === 0 && (
                <tr>
                  <td className="p-4 text-muted-foreground" colSpan={6}>
                    No audit logs found.
                  </td>
                </tr>
              )}
              {!loading &&
                rows.map((row) => {
                  const confidence = (row.confidence_band || 'unknown').toLowerCase();
                  const lowConfidence = confidence === 'low';
                  return (
                    <tr
                      key={row.id}
                      onClick={() => openSessionReview(row)}
                      className={`border-t cursor-pointer hover:bg-muted/30 ${lowConfidence ? 'bg-red-50/60' : ''}`}
                    >
                      <td className="p-3 whitespace-nowrap">
                        {new Date(row.created_at).toLocaleString()}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2 items-center">
                          <Badge variant="outline">{row.decision_type}</Badge>
                          {row.override_applied && <Badge variant="destructive">Overridden</Badge>}
                        </div>
                      </td>
                      <td className="p-3 max-w-sm">
                        <p className="line-clamp-2">{row.input_summary || 'N/A'}</p>
                      </td>
                      <td className="p-3 max-w-sm">
                        <p className="line-clamp-2">{row.output_summary || 'N/A'}</p>
                      </td>
                      <td className="p-3">
                        <Badge
                          variant="outline"
                          className={
                            confidence === 'low'
                              ? 'text-red-700 border-red-300 bg-red-100'
                              : confidence === 'medium'
                                ? 'text-amber-700 border-amber-300 bg-amber-100'
                                : 'text-green-700 border-green-300 bg-green-100'
                          }
                        >
                          {row.confidence_band || 'unknown'}
                        </Badge>
                      </td>
                      <td className="p-3">{row.model_name}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" onClick={() => setPage((v) => Math.max(1, v - 1))} disabled={page <= 1 || loading}>
          Previous
        </Button>
        <Button
          variant="outline"
          onClick={() => setPage((v) => Math.min(totalPages, v + 1))}
          disabled={page >= totalPages || loading}
        >
          Next
        </Button>
      </div>

      <SessionReviewDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        audit={selectedAudit}
        onFeedbackSaved={() => void loadRows()}
      />
    </div>
  );
}

