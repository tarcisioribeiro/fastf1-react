import './Table.css';

interface Column {
  key: string;
  label: string;
  align?: 'left' | 'center' | 'right';
}

interface TableProps {
  columns: Column[];
  data: any[];
  highlightTop3?: boolean;
}

export default function Table({ columns, data, highlightTop3 = false }: TableProps) {
  const getRowClass = (index: number) => {
    if (!highlightTop3) return '';
    if (index === 0) return 'row-gold';
    if (index === 1) return 'row-silver';
    if (index === 2) return 'row-bronze';
    return '';
  };

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={{ textAlign: column.align || 'left' }}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className={getRowClass(index)}>
              {columns.map((column) => (
                <td key={column.key} style={{ textAlign: column.align || 'left' }}>
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
