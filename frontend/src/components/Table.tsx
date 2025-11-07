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
  highlightPositions?: number[];
  showTeamColors?: boolean; // Nova prop para controlar se mostra cores das equipes
}

export default function Table({
  columns,
  data,
  highlightTop3 = false,
  highlightPositions = [],
  showTeamColors = true
}: TableProps) {
  const getRowClass = (index: number) => {
    // Se showTeamColors está ativo, não aplicar classes de pódio
    if (showTeamColors) return '';

    if (!highlightTop3 && highlightPositions.length === 0) return '';

    // Use highlightPositions if provided
    if (highlightPositions.length > 0) {
      const position = data[index].position;
      if (highlightPositions.includes(position)) {
        if (position === 1) return 'row-gold';
        if (position === 2) return 'row-silver';
        if (position === 3) return 'row-bronze';
      }
      return '';
    }

    // Fallback to index-based highlighting
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
          {data.map((row, index) => {
            const teamColor = row.teamColor;
            const rowClass = getRowClass(index);

            return (
              <tr
                key={index}
                className={rowClass}
                style={showTeamColors && teamColor ? {
                  borderLeft: `5px solid ${teamColor}`
                } : undefined}
              >
                {columns.map((column, colIndex) => (
                  <td
                    key={column.key}
                    style={{
                      textAlign: column.align || 'left',
                      paddingLeft: colIndex === 0 && showTeamColors && teamColor ? '12px' : undefined
                    }}
                  >
                    {row[column.key]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
