using NUnit.Framework;
using System.Reflection;
using System.Runtime.InteropServices;

[assembly: AssemblyTitle("iText.Barcodes.Tests")]
[assembly: AssemblyDescription("")]
[assembly: AssemblyConfiguration("")]

[assembly: ComVisible(false)]

[assembly: Guid("d015a3aa-613c-45d9-b908-7d47c4b613af")]

[assembly: Parallelizable(ParallelScope.ContextMask)]

#if !NETSTANDARD2_0
[assembly: NUnit.Framework.Timeout(300000)]
#endif
